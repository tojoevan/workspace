from django.core.management.base import BaseCommand
from django.utils import timezone
from rss.models import RSSFeed
import feedparser


class Command(BaseCommand):
    help = '更新所有活跃的 RSS 订阅源'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制更新所有订阅源（包括非活跃的）',
        )
        parser.add_argument(
            '--feed-id',
            type=int,
            help='只更新指定 ID 的订阅源',
        )

    def handle(self, *args, **options):
        force = options['force']
        feed_id = options.get('feed_id')

        # 获取要更新的订阅源
        if feed_id:
            feeds = RSSFeed.objects.filter(id=feed_id)
            if not feeds.exists():
                self.stderr.write(self.style.ERROR(f'订阅源 ID {feed_id} 不存在'))
                return
        elif force:
            feeds = RSSFeed.objects.all()
        else:
            feeds = RSSFeed.objects.filter(is_active=True)

        total_feeds = feeds.count()
        if total_feeds == 0:
            self.stdout.write('没有需要更新的订阅源')
            return

        self.stdout.write(f'开始更新 {total_feeds} 个订阅源...')

        success_count = 0
        error_count = 0
        total_articles = 0

        for feed in feeds:
            try:
                self.stdout.write(f'正在更新: {feed.title} ({feed.url})')

                feed_data = feedparser.parse(feed.url)

                # 检查解析是否成功
                if hasattr(feed_data, 'bozo_exception') and feed_data.bozo:
                    self.stderr.write(self.style.WARNING(
                        f'解析警告 [{feed.title}]: {feed_data.bozo_exception}'
                    ))

                # 获取文章
                article_count = self._fetch_articles(feed, feed_data)

                # 更新最后获取时间
                feed.last_fetched = timezone.now()
                feed.save()

                success_count += 1
                total_articles += article_count
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ {feed.title}: {article_count} 篇文章'
                ))

            except Exception as e:
                error_count += 1
                self.stderr.write(self.style.ERROR(
                    f'  ✗ {feed.title}: {str(e)}'
                ))

        # 输出总结
        self.stdout.write()
        self.stdout.write(self.style.SUCCESS(
            f'更新完成: 成功 {success_count}/{total_feeds}, '
            f'共 {total_articles} 篇文章'
        ))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(
                f'失败 {error_count} 个订阅源'
            ))

    def _fetch_articles(self, feed, feed_data):
        """获取订阅源文章"""
        from django.utils.dateparse import parse_datetime
        from datetime import datetime, timezone as dt_timezone
        import re

        article_count = 0

        for entry in feed_data.entries[:50]:  # 最多获取 50 篇
            # 获取发布时间
            published_at = self._parse_published_time(entry)

            # 获取内容
            content = self._get_entry_content(entry)

            # 获取摘要
            description = self._get_entry_description(entry, content)

            # 获取链接
            link = self._get_entry_link(entry)

            # 获取标题
            title = ''
            if hasattr(entry, 'title') and entry.title:
                title = re.sub(r'<[^>]+>', '', entry.title)
            if not title:
                title = '无标题'

            # 获取作者
            author = ''
            if hasattr(entry, 'author') and entry.author:
                author = entry.author[:100]
            elif hasattr(entry, 'author_detail') and entry.author_detail:
                author = entry.author_detail.get('name', '')[:100] if isinstance(entry.author_detail, dict) else str(entry.author_detail)[:100]

            # 创建或更新文章
            if link:
                from rss.models import RSSArticle
                _, created = RSSArticle.objects.get_or_create(
                    feed=feed,
                    link=link[:2000],
                    defaults={
                        'title': title[:500],
                        'description': description[:2000],
                        'content': content[:10000],
                        'author': author[:100],
                        'published_at': published_at,
                    }
                )
                if created:
                    article_count += 1

        return article_count

    def _parse_published_time(self, entry):
        """解析文章发布时间"""
        from django.utils import timezone
        from django.utils.dateparse import parse_datetime
        from datetime import datetime, timezone as dt_timezone

        published_at = None

        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=dt_timezone.utc)
            except (ValueError, TypeError):
                pass

        if not published_at and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                published_at = datetime(*entry.updated_parsed[:6], tzinfo=dt_timezone.utc)
            except (ValueError, TypeError):
                pass

        if not published_at and hasattr(entry, 'published') and entry.published:
            try:
                published_at = parse_datetime(entry.published)
            except:
                pass

        if not published_at and hasattr(entry, 'updated') and entry.updated:
            try:
                published_at = parse_datetime(entry.updated)
            except:
                pass

        return published_at or timezone.now()

    def _get_entry_content(self, entry):
        """获取文章内容"""
        content = ''

        if hasattr(entry, 'content') and entry.content:
            if isinstance(entry.content, list) and len(entry.content) > 0:
                content = entry.content[0].get('value', '') if isinstance(entry.content[0], dict) else str(entry.content[0])
            elif isinstance(entry.content, str):
                content = entry.content

        if not content and hasattr(entry, 'content_encoded') and entry.content_encoded:
            content = entry.content_encoded

        if not content and hasattr(entry, 'description') and entry.description:
            content = entry.description

        if not content and hasattr(entry, 'summary') and entry.summary:
            content = entry.summary

        return content[:10000]

    def _get_entry_description(self, entry, content):
        """获取文章摘要"""
        import re

        description = ''
        if hasattr(entry, 'summary') and entry.summary:
            description = entry.summary
        elif hasattr(entry, 'description') and entry.description:
            description = entry.description
        elif content:
            description = content[:500]

        return re.sub(r'<[^>]+>', '', description)[:2000]

    def _get_entry_link(self, entry):
        """获取文章链接"""
        link = ''

        if hasattr(entry, 'link') and entry.link:
            link = entry.link
        elif hasattr(entry, 'links') and entry.links:
            for l in entry.links:
                if isinstance(l, dict) and l.get('rel') == 'alternate':
                    link = l.get('href', '')
                    break
                elif isinstance(l, dict) and l.get('href'):
                    link = l.get('href')
                    break

        return link