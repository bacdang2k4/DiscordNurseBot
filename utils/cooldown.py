import time


class CooldownManager:

    def __init__(self, cooldown_seconds=10):

        self.cooldown_seconds = (
            cooldown_seconds
        )

        self.users = {}


    def check(self, user_id):

        now = time.time()

        last_used = self.users.get(
            user_id
        )

        if last_used is None:

            self.users[user_id] = now

            return True, 0


        elapsed = now - last_used

        if elapsed >= self.cooldown_seconds:

            self.users[user_id] = now

            return True, 0


        remaining = (
            self.cooldown_seconds
            - elapsed
        )

        return False, remaining