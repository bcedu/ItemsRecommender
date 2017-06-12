import argparse
import datetime

from tools.Product import Product, categories_compatibility
from tools.User import User

from tools.Review import Review



def calc_users_similarities(cursor):
    """Calculate and store in database the similarity between all the users from the database"""
    inici = datetime.datetime.now()
    all_users = User.get_all_users(cursor)
    similarities = []
    for userX in all_users:
        reviewsX = Review.get_reviews_from_user(cursor, userX.id)
        for userY in all_users:
            if userX.id != userY.id and not User.already_compared(cursor, userX.id, userY.id):
                reviewsY = Review.get_reviews_from_user(cursor, userY.id)
                similarities += calc_userX_userY_similarity(userX, userY, reviewsX, reviewsY)
            if (datetime.datetime.now() - inici).seconds / 3600 >= 12:
                User.add_similarities(cursor, similarities)
                return 0
    User.add_similarities(cursor, similarities)


def calc_userX_userY_similarity(userX, userY, reviewsX, reviewsY):
    """Return a tuple with (userX, userY, similarity). The similarity between userX and userY is
    calculated with the Jaccard distance using the reviews made by both users."""
    similarities = []
    m11 = 0
    m10 = 0
    m01 = 0
    limit = 1
    for reviewX in reviewsX:
        reviewY = None
        for review_aux in reviewsY:
            if review_aux.product_id == reviewX.product_id:
                reviewY = review_aux
                break
        if reviewY:
            if (reviewX.overall - reviewY.overall) > limit:
                m10 += 4
            elif (reviewY.overall - reviewX.overall) > limit:
                m01 += 4
            elif abs(reviewY.overall - reviewX.overall) <= limit:
                m11 += 4
            else:
                print("ERROR jaccard similarity {0} - {1}"
                      .format(reviewX.product_id, reviewY.product_id))
        else:
            if reviewX.overall <= 2:
                m11 += 1
            else:
                m10 += 1
    for reviewY in reviewsY:
        reviewX = None
        for review_aux in reviewsX:
            if review_aux.product_id == reviewY.product_id:
                reviewX = review_aux
                break
        if not reviewX:
            if reviewY.overall <= 2:
                m11 += 1
            else:
                m01 += 1
    similarity_XY = 0
    if m10 + m01 + m11 != 0:
        similarity_XY = m11 / (m10 + m01 + m11)
    similarities.append((userX.id, userY.id, similarity_XY))
    return similarities


def calc_purchase_probability(cr, uid, pid, u_number):
    """Return the probability for user 'uid' of buying the product 'pid'.
    It is calculed by checking the reviews of the 'u_number' most similar users."""
    similar_users_sim = User.get_user_x_most_similar_users(cr, uid, u_number)
    prod_reviews = Review.get_reviews_from_product(cr, pid)
    num_accum = 0
    den_accum = 0
    for user_sim in similar_users_sim:
        r = 0
        for review in prod_reviews:
            if review.user_id == user_sim[0]:
                r = (review.overall * 2) / 10
                break
        num_accum += user_sim[1] * r
        den_accum += user_sim[1]
    return num_accum / den_accum


def calc_all_products_compatibility(cr):
    """Calculate and store in database the compatibility between all the products from the database."""
    inici = datetime.datetime.now()
    all_products = Product.get_all_products(cr)
    for p in all_products:
        for p2 in all_products:
            if p.id != p2.id and not Product.compatibility(cr, p.id, p2.id):
                comp = calc_2_products_compatibility(cr, p, p2)
                Product.add_compatibility(cr, p.id, p2.id, comp)
        if ((datetime.datetime.now() - inici).seconds / 3600) >= 15:
            break


def calc_2_products_compatibility(cr, prod1, prod2):
    """Return compatibility between prod1 and prod2.
    It's calculated with the Jaccard distance checking the brand, category and bought_together list."""
    m11 = 0
    m00 = 0
    if prod1.brand and prod2.brand:
        if prod1.brand == prod2.brand:
            m11 += 4
        else:
            m00 += 4
    if prod1.id in prod2.also_bought or prod2.id in prod1.also_bought:
        m11 += 3
    else:
        m00 += 3
    if prod1.id in prod2.bought_together or prod2.id in prod1.bought_together:
        m11 += 6
    else:
        no_trobat = 6
        for aux_id in prod2.bought_together:
            aux = Product.get_product_from_asin(cr, aux_id)
            if aux:
                if prod1.id in aux.bought_together or aux.id in prod1.bought_together:
                    m11 += 3
                    no_trobat = 0
                    break
        for aux_id in prod1.bought_together:
            aux = Product.get_product_from_asin(cr, aux_id)
            if aux:
                if prod2.id in aux.bought_together or aux.id in prod2.bought_together:
                    m11 += 3
                    no_trobat = 0
                    break
        m00 += no_trobat
    if prod2.table_name in categories_compatibility[prod1.table_name] or prod1.table_name in \
            categories_compatibility[prod2.table_name]:
        m11 += 4
    else:
        m00 += 4
    return m11 / (m11 + m00)


def get_static_bundle_recomendation(cr, user, product, num_users, bundle_size, levels):
    """Returns a recommendation of a bundle of 'bundle_size' products for a user and a product.
    Recommendated products are calculated using static recommendation."""
    comp_products = get_static_compatible_products(cr, product.id, levels)
    products_sumary = []
    for pc in comp_products:
        products_sumary.append((pc, calc_purchase_probability(cr, user.id, pc, num_users)))
    return sorted(products_sumary, key=lambda t: t[1], reverse=True)[0:bundle_size]


def get_static_compatible_products(cr, pid, levels):
    """Return the products found in 'bought_together' and 'also_bought' of 'pid'. The method is called recursivly
    for each product found in 'bought_together' 'level' times."""
    p = Product.get_product_from_asin(cr, pid)
    trobats = []
    for bt in p.bought_together+p.also_bought:
        p2 = Product.get_product_from_asin(cr, bt)
        if p2:
            if p2.id not in trobats:
                trobats.append(p2.id)
            if levels > 0:
                for t in get_static_compatible_products(cr, p2.id, levels - 1):
                    if t not in trobats and t != p.id:
                        trobats.append(t)
    return trobats


def get_dinamic_bundle_recomendation(cr, user, product, num_users, bundle_size, comp):
    """Returns a recommendation of a bundle of 'bundle_size' products for a user and a product.
        Recommendated products are calculated using dinamic recommendation."""
    comp_products = get_dinamic_compatible_products(cr, product.id, bundle_size*20, comp)
    products_sumary = []
    for pc in comp_products:
        res = evaluar(pc[1], calc_purchase_probability(cr, user.id, pc[0], num_users))
        products_sumary.append((pc[0], res))
    return sorted(products_sumary, key=lambda t: t[1], reverse=True)[0:bundle_size]


def evaluar(comp, prob):
    return comp * (2 * prob)


def get_dinamic_compatible_products(cr, pid, nproducts, comp):
    """Returns the nproducts most compatible products of pid."""
    return Product.get_product_x_most_compatible_products(cr, pid, num=nproducts, compatibility=comp)


def login(cr, uid):
    """Return the User uid."""
    user = User.get_user_from_id(cr, uid)
    while not user:
        print("Wrong user ID, '\q' to quit or try again:")
        inp = input()
        if inp == '\q':
            break
        user = User.get_user_from_id(cr, inp)
    return user


def buy_product(cr, pid):
    """Return the Product pid."""
    product = Product.get_product_from_asin(cr, pid)
    while not product:
        print("Wrong product asin, '\q' to quit or try again:")
        inp = input()
        if inp == '\q':
            break
        product = Product.get_product_from_asin(cr, inp)
    return product


def main(args):
    from Loader import Loader
    loader = Loader(new_bd=False, db_name=args.database)
    cursor = loader.cursor

    user = login(cursor, args.user)
    if not user:
        return 0
    product = buy_product(cursor, args.product)
    if not product:
        return 0

    if args.dinamic is None:
        result = get_static_bundle_recomendation(cursor, user, product, args.num_users, args.bundle_size, 3)
    else:
        result = get_dinamic_bundle_recomendation(cursor, user, product, args.num_users, args.bundle_size,
                                                  args.dinamic)

    print("\nYou bought a {0} ({1}), why don't you buy this too:".format(product.title, product.id))
    for r in result:
        p = Product.get_product_from_asin(cursor, r[0])
        print("  > {0} ({1})".format(p.title, p.id))
    print("")
    loader.disconnect_database()
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-db", "--database", default='recommender.db',
                        help="Database name. Database must be in 'resources' directory. By default it's 'recommender.db'.")
    parser.add_argument("-u", "--user", help="User ID.")
    parser.add_argument("-p", "--product", help="Product Asin.")
    parser.add_argument("-b", "--bundle_size", type=int, default=3,
                        help="Number of products to recommend. Bt default it's 3.")
    parser.add_argument("-n", "--num_users", type=int, default=10,
                        help="Number of users used to compare with and make the recommendation. By default it's 10.")
    parser.add_argument("-d", "--dinamic", type=float,
                        help="Make dinamic recommendation by getting products with a compatibility >= DINAMIC. By default recommendations are made using the static method.")
    main(parser.parse_args())
