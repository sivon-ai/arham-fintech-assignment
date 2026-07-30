from apscheduler.schedulers.background import BackgroundScheduler

from app.scheduler.jobs import sync_job

scheduler = BackgroundScheduler()


def start_scheduler():

    scheduler.add_job(

        func=sync_job,

        trigger="interval",

        minutes=1,

        id="bse_sync",

        max_instances=1,

        replace_existing=True,

        coalesce=True

    )

    scheduler.start()

    print("Scheduler Started")


def stop_scheduler():

    scheduler.shutdown(wait=False)

    print("Scheduler Stopped")