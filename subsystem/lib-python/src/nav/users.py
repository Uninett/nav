def loadUser(login):
    user = User(login, "eggs")
    # Should retrieve this info from the database instead.
    return user

class User:
    def __init__(self, login, password):
        self.login = login
        self._password = password

    def authenticate(self, password):
        """Return True if the user's password matches the given string"""
        if self._password == password:
            return True
        else:
            return False
