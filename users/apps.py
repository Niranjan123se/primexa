from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):
        # Registers audit handlers after Django has loaded its app registry.
        from . import signals  # noqa: F401
