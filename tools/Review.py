from datetime import datetime

rates_table_names = [
    'cellphones_rates',
    'clothing_rates',
    'music_rates',
    'electronics_rates',
    'movies_rates',
    'musical_instruments_rates',
    'videogame_rates',
    'sports_rates',
]


class Review(object):

    def __init__(self, id, product_id, overall, review_text, review_time, user_id, user_name, summary):
        self.id = id
        self.product_id = product_id
        self.overall = overall
        self.review_text = review_text
        self.review_time = review_time
        self.user_id = user_id
        self.user_name = user_name
        self.summary = summary

    @staticmethod
    def change_owner(cr, uid, new_uid):
        """Set the 'user_id' of all the reviews made by 'uid' to 'new_uid'."""
        for table_name in rates_table_names:
                cr.execute("UPDATE {0} SET user_id = '{1}' WHERE user_id = '{2}';"
                           .format(table_name, new_uid, uid))

    @staticmethod
    def get_reviews_from_product(cr, pid, table_name=None):
        """Returns all the reviews about product 'pid'."""
        trobats = []
        if table_name:
            rs = cr.execute("SELECT * FROM {1} WHERE product_id = '{0}';".format(pid, table_name))
            for r in rs:
                trobats.append(Review(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
        else:
            for table_name in rates_table_names:
                rs = cr.execute("SELECT * FROM {1} WHERE product_id = '{0}';".format(pid, table_name))
                for r in rs:
                    trobats.append(Review(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
        return trobats

    @staticmethod
    def get_reviews_from_user(cr, uid, table_name=None):
        """Returns all the reviews made by user 'uid'."""
        trobats = []
        if table_name:
            rs = cr.execute("SELECT * FROM {1} WHERE user_id = '{0}';".format(uid, table_name))
            for r in rs:
                trobats.append(Review(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
        else:
            for table_name in rates_table_names:
                rs = cr.execute("SELECT * FROM {1} WHERE user_id = '{0}';".format(uid, table_name))
                for r in rs:
                    trobats.append(Review(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
        return trobats

    @staticmethod
    def get_first_review_from_user(cr, uid, table_name=None):
        """Get the most recent review made by user 'uid'."""
        date = datetime.strptime("01 01, 2900", '%m %d, %Y')
        r_act = []
        if table_name:
            rs = cr.execute("SELECT * FROM {1} WHERE user_id = '{0}';".format(uid, table_name))
            for r in rs:
                date2 = datetime.strptime(r[4], '%m %d, %Y')
                if date2 < date:
                    date = date2
                    r_act = r
        else:
            for table_name in rates_table_names:
                rs = cr.execute("SELECT * FROM {1} WHERE user_id = '{0}';".format(uid, table_name))
                for r in rs:
                    date2 = datetime.strptime(r[4], '%m %d, %Y')
                    if date2 < date:
                        date = date2
                        r_act = r
        if r_act:
            return Review(r_act[0], r_act[1], r_act[2], r_act[3], r_act[4], r_act[5], r_act[6], r_act[7])
        return None

    @staticmethod
    def get_review_from_user_product(cr, uid, pid):
        for table_name in rates_table_names:
            rs = cr.execute("SELECT * FROM {2} WHERE product_id = '{0}' AND user_id='{1}';".format(pid, uid, table_name))
            r = rs.fetchone()
            if r:
                return Review(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7])
