from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = '核心模块'

    def ready(self):
        import os
        # 仅在 runserver / gunicorn 主进程运行调度器
        if os.environ.get('RUN_MAIN', None) != 'true' and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from django.core.management import call_command
            import logging

            logger = logging.getLogger(__name__)

            scheduler = BackgroundScheduler()

            def update_feeds_job():
                logger.info('[Scheduler] Running update_rss...')
                try:
                    call_command('update_rss')
                except Exception as e:
                    logger.error(f'[Scheduler] update_rss failed: {e}')

            # 默认每 30 分钟执行一次
            interval_minutes = int(os.environ.get('RSS_FETCH_INTERVAL', 30))
            scheduler.add_job(
                update_feeds_job,
                'interval',
                minutes=interval_minutes,
                id='update_rss',
                replace_existing=True,
            )

            scheduler.start()
            logger.info(f'[Scheduler] Started, update_rss every {interval_minutes}min')

        except ImportError as e:
            pass
