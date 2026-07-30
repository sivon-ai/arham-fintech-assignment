from threading import Thread

from apscheduler.schedulers.background import BackgroundScheduler

from app.scheduler.jobs import sync_job

scheduler = BackgroundScheduler()


def start_scheduler(run_immediately=True):
    if scheduler.running:
        return

    scheduler.add_job(
        func=sync_job,
        trigger="interval",
        minutes=1,
        id="bse_sync",
        max_instances=1,
        replace_existing=True,
        coalesce=True,
    )
    scheduler.start()

    if run_immediately:
        Thread(target=sync_job, daemon=True).start()

    print("Scheduler Started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("Scheduler Stopped")
