class User(object):

    def __init__(self, uid, uname):
        self.id = uid
        self.name = uname

    @staticmethod
    def get_user_from_id(cr, uid):
        """Returns the User with id == uid."""
        u = cr.execute("SELECT id, name FROM users_data WHERE id = '{0}';".format(uid))
        u = u.fetchone()
        try:
            return User(u[0], u[1])
        except:
            return None

    @staticmethod
    def already_compared(cr, userX, userY):
        """Returns True if userX and userY have a simimlarity stored in database."""
        us = cr.execute("SELECT id FROM user_similarities WHERE userX='{0}' AND userY='{1}';".format(userX, userY))
        if not us.fetchone():
            return False
        return True

    @staticmethod
    def get_all_users(cr):
        """Returns all the Users from the  database."""
        trobats = []
        us = cr.execute("SELECT id, name FROM users_data;")
        for u in us:
            trobats.append(User(u[0], u[1]))
        return trobats

    @staticmethod
    def add_similarities(cr, similarities):
        """Add new simimlarity to database."""
        for sim in similarities:
            cr.execute("INSERT INTO user_similarities (userX, userY, similarity) "
                       "VALUES (?, ?, ?)", (sim[0], sim[1], sim[2]))

    @staticmethod
    def get_user_x_most_similar_users(cr, userX, num=None):
        """Returns the 'num' most similar users of userX."""
        trobats = []
        i = 0
        rs = cr.execute("SELECT userY, similarity FROM user_similarities WHERE userX = '{0}' ORDER BY similarity DESC;".format(userX))
        for r in rs:
            trobats.append((r[0], r[1]))
            if num:
                i += 1
            if num and i >= num:
                break
        return trobats
