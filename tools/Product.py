meta_table_names = [
    'cellphones_meta',
    'clothing_meta',
    'music_meta',
    'electronics_meta',
    'movies_meta',
    'musical_instruments_meta',
    'videogame_meta',
    'sports_meta',
]

categories_compatibility = {
    "cellphones_meta": ["cellphones_meta", "electronics_meta", "music_meta", "videogame_meta"],
    "clothing_meta": ["clothing_meta", "sports_meta"],
    "music_meta": ["music_meta", "musical_instruments_meta", "cellphones_meta", "movies_meta"],
    "electronics_meta": ["electronics_meta", "cellphones_meta", "videogame_meta", "movies_meta"],
    "movies_meta": ["movies_meta", "electronics_meta", "music_meta"],
    "musical_instruments_meta": ["musical_instruments_meta", "music_meta"],
    "videogame_meta": ["videogame_meta", "cellphones_meta", "electronics_meta"],
    "sports_meta": ["sports_meta", "clothing_meta"]
}


class Product(object):

    def __init__(self, id, title, price, also_bought, also_viewed, bought_together, sales_rank, brand, categories, tn):
        self.id = id
        self.title = title
        self.price = price
        try: self.also_bought = also_bought.replace(" ", "").replace(",,", ",").split(',')
        except: self.also_bought = []
        try: self.also_viewed = also_viewed.replace(" ", "").replace(",,", ",").split(',')
        except: self.also_viewed = []
        try: self.bought_together = bought_together.replace(" ", "").replace(",,", ",").split(',')
        except: self.bought_together = []
        self.sales_rank = sales_rank
        self.brand = brand
        try: self.categories = categories.split(',')
        except: self.categories = []
        self.table_name = tn

    @staticmethod
    def get_product_from_asin(cr, pid, table_name=None):
        """Returns the Product with id == pid."""
        if table_name:
            p = cr.execute("SELECT * FROM {1} WHERE id = '{0}';".format(pid, table_name))
            p = p.fetchone()
        else:
            for table_name in meta_table_names:
                p = cr.execute("SELECT * FROM {1} WHERE id = '{0}';".format(pid, table_name))
                p = p.fetchone()
                if p is not None:
                    break
        try:
            return Product(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9])
        except:
            return None

    @staticmethod
    def get_all_products(cr, table_name=None):
        """Returns all the Products from the  database."""
        trobats = []
        if table_name:
            ps = cr.execute("SELECT * FROM {0};".format(table_name))
            for p in ps:
                trobats.append(Product(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9]))
        else:
            for table_name in meta_table_names:
                ps = cr.execute("SELECT * FROM {0};".format(table_name))
                for p in ps:
                    trobats.append(Product(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9]))
        return trobats

    @staticmethod
    def compatibility(cr, pid1, pid2):
        """Returns the compatibility between pid1 and pid2."""
        c = cr.execute("SELECT compatibility from product_compatibilities WHERE (productX = '{0}' and productY = '{1}');".format(pid1, pid2))
        c = c.fetchone()
        if c:
            return c[0]
        else:
            return None

    @staticmethod
    def add_compatibility(cr, pid1, pid2, comp):
        """Add new compatibility to database."""
        cr.execute("INSERT INTO product_compatibilities (productX, productY, compatibility) "
                   "VALUES (?, ?, ?)", (pid1, pid2, comp))

    @staticmethod
    def get_product_x_most_compatible_products(cr, productX, num, compatibility=None):
        """Returns the 'num' most compatible products of pid tha have a compatibility >= 'compatibility'."""
        trobats = []
        i = 0
        if not compatibility:
            compatibility = 0
        rs = cr.execute("SELECT productY, compatibility FROM product_compatibilities WHERE productX = '{0}' ORDER BY compatibility DESC;".format(productX))
        for r in rs:
            if compatibility:
                if r[1] >= compatibility:
                    trobats.append((r[0], r[1]))
                    i += 1
                else:
                    break
            else:
                trobats.append((r[0], r[1]))
                i += 1
            if i >= num:
                break
        return trobats
