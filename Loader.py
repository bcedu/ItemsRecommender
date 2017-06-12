import argparse
import os
import sqlite3
from datetime import datetime
from random import randint

from tools.Product import Product
from tools.User import User

from Recommender import calc_users_similarities, calc_all_products_compatibility
from tools.Review import Review

RESOURCES_PATH = "./resources/"
CELLPHONES = ["Cell_Phones_and_Accessories_5.json", "meta_Cell_Phones_and_Accessories.json"]
CLOTHING = ["Clothing_Shoes_and_Jewelry_5.json", "meta_Clothing_Shoes_and_Jewelry.json"]
MUSIC = ["Digital_Music_5.json", "meta_Digital_Music.json"]
ELECTRONICS = ["Electronics_5.json", "meta_Electronics.json"]
MOVIES = ["Movies_and_TV_5.json", "meta_Movies_and_TV.json"]
MUSICAL_INSTRUMENTS = ["Musical_Instruments_5.json", "meta_Musical_Instruments.json"]
VIDEOGAME = ["Video_Games_5.json", "meta_Video_Games.json"]
SPORTS = ["Sports_and_Outdoors_5.json", "meta_Sports_and_Outdoors.json"]


class Loader(object):

    db_connection = None
    cursor = None
    path = ""

    def __init__(self, modifier=None, new_bd=None, db_name='recommender.db'):
        self.path = RESOURCES_PATH+db_name
        if not os.path.exists(self.path) and new_bd:
            self.create_db_data(modifier)
        elif os.path.exists(self.path) and not new_bd:
            self.connect_database()
        else:
            print(new_bd)
            print(self.path)
            print("ERROR creating Loader")

    def connect_database(self):
        """Set the cursor and open a db_connection."""
        self.db_connection = sqlite3.connect(self.path)
        self.cursor = self.db_connection.cursor()

    def disconnect_database(self):
        """Disconnect from database without commiting."""
        self.cursor.close()
        self.db_connection.close()

    def disconnect_and_save_database(self):
        """Disconnect from database and commit changes."""
        self.cursor.close()
        self.db_connection.commit()
        self.db_connection.close()

    def create_db_data(self, modifier):
        """Create a new database from 'tiny_{modifier}_{original_name}.json' files found in directory 'resources'.
        The new db will be named 'recommender.db'."""
        # Delete previous DB
        try:
            os.remove(self.path)
            print("Base de dades previa borrada")
        except:
            print("No existia base de dades previa.")

        # Create new DB
        self.db_connection = sqlite3.connect(self.path)
        self.cursor = self.db_connection.cursor()
        # Create en empty table for users
        self.create_users_table(self.cursor)

        # Create en empty table for categories
        self.create_categories_table(self.cursor)

        # Create en empty table for user_similarities
        self.create_user_similarities_table(self.cursor)

        # Create en empty table for product_compatibilities
        self.create_product_compatibilities_table(self.cursor)

        # Create tables of metadata, rating and users from a file
        self.create_tables_from_file(
            "cellphones", RESOURCES_PATH + modifier + CELLPHONES[1],
            RESOURCES_PATH + modifier + CELLPHONES[0], self.cursor
        )
        self.create_tables_from_file(
            "clothing", RESOURCES_PATH + modifier + CLOTHING[1],
                      RESOURCES_PATH + modifier + CLOTHING[0], self.cursor
        )
        self.create_tables_from_file(
            "music", RESOURCES_PATH + modifier + MUSIC[1],
                      RESOURCES_PATH + modifier + MUSIC[0], self.cursor
        )
        self.create_tables_from_file(
            "electronics", RESOURCES_PATH + modifier + ELECTRONICS[1],
                      RESOURCES_PATH + modifier + ELECTRONICS[0], self.cursor
        )
        self.create_tables_from_file(
            "movies", RESOURCES_PATH + modifier + MOVIES[1],
                      RESOURCES_PATH + modifier + MOVIES[0], self.cursor
        )
        self.create_tables_from_file(
            "musical_instruments", RESOURCES_PATH + modifier + MUSICAL_INSTRUMENTS[1],
                      RESOURCES_PATH + modifier + MUSICAL_INSTRUMENTS[0], self.cursor
        )
        self.create_tables_from_file(
            "videogame", RESOURCES_PATH + modifier + VIDEOGAME[1],
                      RESOURCES_PATH + modifier + VIDEOGAME[0], self.cursor
        )
        self.create_tables_from_file(
            "sports", RESOURCES_PATH + modifier + SPORTS[1],
                      RESOURCES_PATH + modifier + SPORTS[0], self.cursor
        )
        # delete unnecessary users
        # self.delete_unnecessary_users(self.cursor)
        self.db_connection.commit()
        return self.db_connection

    def create_users_table(self, cr):
        """Creates the table of Users."""
        cr.execute("CREATE TABLE users_data (id TEXT PRIMARY KEY, name TEXT);")

    def create_categories_table(self, cr):
        """Creates the table of Categories."""
        cr.execute("CREATE TABLE categories_data (name TEXT PRIMARY KEY);")

    def create_user_similarities_table(self, cr):
        """Creates the table of User Similarities."""
        cr.execute("CREATE TABLE user_similarities ("
                   "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                   "userX TEXT,"
                   "userY TEXT,"
                   "similarity FLOAT,"
                   "FOREIGN KEY (userX) REFERENCES users_data(id),"
                   "FOREIGN KEY (userY) REFERENCES users_data(id));")

    def create_product_compatibilities_table(self, cr):
        """Creates the table of Products Compatibilities."""
        cr.execute("CREATE TABLE product_compatibilities ("
                   "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                   "productX TEXT,"
                   "productY TEXT,"
                   "compatibility FLOAT);")

    def create_tables_from_file(self, table_name, path_meta, path_rates, cr):
        """Creates the tables of Products and Reviews."""
        self.create_meta_table(table_name+"_meta", path_meta, cr)
        self.create_rating_table(table_name+"_rates", table_name+"_meta", path_rates, cr)

    def create_meta_table(self, table_name, path_meta, cr):
        """Create the metadata table of this kind of products.
        If a new category is found it is added to categories_data"""
        cr.execute("CREATE TABLE {} ("
                   "id TEXT PRIMARY KEY, "
                   "title TEXT, "
                   "price REAL, "
                   "also_bought TEXT, "
                   "also_viewed TEXT, "
                   "bought_together TEXT, "
                   "sales_rank TEXT, "
                   "brand TEXT, "
                   "categories TEXT,"
                   "table_name TEXT);"
                   .format(table_name))
        parsed = self.parse(path_meta)
        for data in parsed:
            title = None
            if 'title' in data.keys():
                title = data['title']
            price = None
            if 'price' in data.keys():
                price = data['price']
            also_bought = None
            also_viewed = None
            bought_together = None
            if 'related' in data.keys():
                if 'also_bought' in data['related'].keys():
                    also_bought = "".join([x + ", " for x in data['related']['also_bought'] if x != " " and x != ""])
                if 'also_viewed' in data['related'].keys():
                    also_viewed = "".join([x + ", " for x in data['related']['also_viewed']])
                if 'bought_together' in data['related'].keys():
                    bought_together = "".join([x + ", " for x in data['related']['bought_together']])
            sales = None
            if 'salesRank' in data.keys():
                sales = "".join([x + ": " + str(data['salesRank'][x]) + ", " for x in data['salesRank'].keys()])
            brand = None
            if 'brand' in data.keys():
                brand = data['brand']
            categories = None
            if 'categories' in data.keys():
                categories = "".join([str(x) + ", " for x in data['categories'][0]])
                for cat in data['categories'][0]:
                    try:
                        cr.execute("INSERT INTO categories_data (name) VALUES (?);", ([cat]))
                    except: pass

            cr.execute("INSERT INTO {} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);".format(table_name),
                       (data['asin'], title, price, also_bought, also_viewed, bought_together,
                        sales, brand, categories, table_name))

    def create_rating_table(self, table_name, table_name_meta, path_ratings, cr):
        """Create a reviews table of this kind of products.
        If a new user is found it is added to users_data."""
        cr.execute("CREATE TABLE {0} ("
                   "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                   "product_id TEXT, "
                   "overall REAL, "
                   "review_text TEXT, "
                   "review_time TEXT, "
                   "user_id TEXT, "
                   "user_name TEXT, "
                   "summary TEXT, "
                   "FOREIGN KEY (product_id) REFERENCES {1}(id), "
                   "FOREIGN KEY (user_id) REFERENCES users_data(id));"
                   .format(table_name, table_name_meta))
        parsed = self.parse(path_ratings)
        for data in parsed:
            overall = None
            if 'overall' in data.keys():
                overall = data['overall']
            review_text = None
            if 'reviewText' in data.keys():
                review_text = data['reviewText']
            review_time = None
            if 'reviewTime' in data.keys():
                review_time = data['reviewTime']
            reviewer_id = None
            if 'reviewerID' in data.keys():
                reviewer_id = data['reviewerID']
            reviewer_name = None
            if 'reviewerName' in data.keys():
                reviewer_name = data['reviewerName']
            summary = None
            if 'summary' in data.keys():
                summary = data['summary']
            try:
                cr.execute("INSERT INTO users_data VALUES (?, ?)", (reviewer_id, reviewer_name))
            except: pass
            cr.execute("INSERT INTO {} (product_id, overall, review_text, review_time, user_id, user_name, summary) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?)".format(table_name),
                       (data['asin'], overall, review_text, review_time,
                        reviewer_id, reviewer_name, summary))

    def cut_users(self, cr, num):
        """Delete Users from database until have only 'num' users.
        The reviews from the deleted users are randomly assigned to the remining users."""
        users = User.get_all_users(cr)
        num_users = len(users)
        for i in range(num_users-num):
            new_owner = randint(num_users-num, num_users-1)
            Review.change_owner(cr, users[i].id, users[new_owner].id)
            cr.execute("DELETE FROM users_data WHERE id = '{0}'".format(users[i].id))

    def extend_products_from_db(self, cr, other_db_path, p_table_name=None):
        """Extend the database by adding all the products found in the 'bought_together' atribute of Products.
        The new products, users and reviews will be taken from the original database 'recommender_backup.db'."""
        db_connection_2 = sqlite3.connect(other_db_path)
        cr2 = db_connection_2.cursor()
        inici = datetime.now()
        if not p_table_name:
            products = Product.get_all_products(cr)
        else:
            products = Product.get_all_products(cr, p_table_name)
        for p in products:
            if ((datetime.now() - inici).seconds / 3600) >= 10:
                return 0
            bts = p.bought_together
            for bt in bts:
                pbt = Product.get_product_from_asin(cr, bt)
                if not pbt:
                    new_p = Product.get_product_from_asin(cr2, bt)
                    if new_p:
                        ab = "".join([x + ", " for x in new_p.also_bought])
                        gt = "".join([x + ", " for x in new_p.bought_together])
                        av = "".join([x + ", " for x in new_p.also_viewed])
                        cat = "".join([x + ", " for x in new_p.categories])
                        cr.execute("INSERT INTO {} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);".format(new_p.table_name),
                                   (new_p.id, new_p.title, new_p.price, ab, av, gt, new_p.sales_rank, new_p.brand, cat, new_p.table_name))
                        table_name = new_p.table_name[0:-4]+"rates"
                        for r in Review.get_reviews_from_product(cr2, new_p.id):
                            cr.execute("INSERT INTO {} (product_id, overall, review_text, review_time, user_id, user_name, "
                                       "summary) VALUES (?, ?, ?, ?, ?, ?, ?)".format(table_name),
                                       (r.product_id, r.overall, r.review_text, r.review_time, r.user_id, r.user_name, r.summary))
                            if not User.get_user_from_id(cr, r.user_id):
                                new_u = User.get_user_from_id(cr2, r.user_id)
                                cr.execute("INSERT INTO users_data VALUES (?, ?)", (new_u.id, new_u.name))

    def parse(self, path):
        g = open(path, 'r')
        for l in g:
            yield eval(l)


def cut_data(paths, number):
    """Generate new '.json' files from the original ones with only NUMBER products.
    The new '.json' files will be named 'tiny_{NUMBER}_{original_name}'."""
    i = 0
    new_rating_ids = []
    big_rates = open(RESOURCES_PATH + paths[0], 'r')
    new_rates = open(RESOURCES_PATH + "tiny_"+str(number)+"_" + paths[0], 'w')
    for l in big_rates:
        elem = eval(l)
        if elem['asin'] not in new_rating_ids and i < number:
            new_rating_ids.append(elem['asin'])
            i += 1
        if elem['asin'] in new_rating_ids:
            new_rates.write(l)
    new_rates.close()
    big_meta = open(RESOURCES_PATH + paths[1], 'r')
    new_meta = open(RESOURCES_PATH + "tiny_"+str(number)+"_" + paths[1], 'w')
    for l in big_meta:
        elem = eval(l)
        if elem['asin'] in new_rating_ids:
            new_meta.write(l)
    new_meta.close()
    return True


def cut_data_to_number(number):
    cut_data(CELLPHONES, number)
    cut_data(CLOTHING, number)
    cut_data(MUSIC, number)
    cut_data(ELECTRONICS, number)
    cut_data(MOVIES, number)
    cut_data(MUSICAL_INSTRUMENTS, number)
    cut_data(VIDEOGAME, number)
    cut_data(SPORTS, number)


def main(args):
    inici = datetime.now()
    print("Started at: {0}".format(inici))

    if args.cut_data:
        cut_data_to_number(args.cut_data)

    if args.new_db:
        new = True
        mod = args.new_db
    else:
        new = False
        mod = ''
    loader = Loader(modifier=mod, new_bd=new)
    cursor = loader.cursor

    if args.extend_products:
        loader.extend_products_from_db(cursor, RESOURCES_PATH+"recommender_backup.db")

    if args.cut_users:
        loader.cut_users(cursor, args.cut_users)

    if args.users_similarities:
        calc_users_similarities(cursor)

    if args.products_compatibilities:
        calc_all_products_compatibility(cursor)

    loader.disconnect_and_save_database()
    final = datetime.now()
    print("Finished at: {0}".format(final))
    print("Time spent: {0}".format(final - inici))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-cd", "--cut_data", type=int, metavar='NUMBER', help="Generate new '.json' files from the original ones with only NUMBER products. The new '.json' files will be named 'tiny_{NUMBER}_{original_name}'.")
    parser.add_argument("-n", "--new_db", metavar='MODIFIER',
                        help="Create a new database from 'tiny_{MODIFIER}_{original_name}.json' files. The new db will be named 'recommender.db'.")
    parser.add_argument("-e", "--extend_products", action="store_true", help="Extend the database by adding all the products found in the 'bought_together' atribute of Products. The new products, users and reviews will be taken from the original database 'recommender_backup.db'.")
    parser.add_argument("-cu", "--cut_users", type=int, metavar='NUMBER', help="Cut the number of users of the database to NUMBER. For each deleted user, his reviews will be randomly assigned to one of the remaining users.")
    parser.add_argument("-us", "--users_similarities", action="store_true", help="Calculate all users similarities and store them in the database.")
    parser.add_argument("-pc", "--products_compatibilities", action="store_true", help="Calculate all products compatibilities and store them in the database.")
    main(parser.parse_args())
