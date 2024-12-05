import os
import django
import dramatiq
from django.conf import settings
from dramatiq.brokers.redis import RedisBroker

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scheduler.settings")

django.setup()

broker = RedisBroker(url=settings.DRAMATIQ_BROKER["OPTIONS"]["url"])
dramatiq.set_broker(broker)

import core.tasks

if __name__ == "__main__":
    from dramatiq.cli import main
    main()