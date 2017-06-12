from argparse import Namespace
from tools.Review import Review, rates_table_names
import Loader
import Recommender

user_test_ids = ['A1GJGQAEQCFZB0', 'A15UAAF89CZCTJ', 'A3S1HDQLL3BLLP', 'AKBVYIIHWI04B', 'A2HTWILZUNAWJ0',
                 'A0266076X6KPZ6CCHGVS', 'A3OVAZG3IK32WC', 'A2RLPCNSPSAQ0', 'A32U48NPM01NIU', 'A2VKBENU2H4VN']
# Connect to test_database and orig_database
test = Loader.Loader(new_bd=False, db_name='recommender.db')
results = {}
for user_test_id in user_test_ids:
    s_recomendations = []
    d_recomendations = []
    s_num_products = 0
    d_num_products = 0

    # Get the first bought product of each category by user in test_database
    first_bought = []
    for table_name in rates_table_names:
        first_from_table = Review.get_first_review_from_user(test.cursor, user_test_id, table_name)
        if first_from_table:
            first_bought.append(first_from_table.product_id)

    # Simulate buying the first_bought products and get static and dinamic recommendations
    for product_id in first_bought:
        static_args = Namespace(database='recommender.db', user=user_test_id, product=product_id, bundle_size=4, num_users=10, dinamic=None)
        s_recomendations.append(Recommender.main(static_args))
        s_num_products += len(s_recomendations[-1])
        dinamic_args = Namespace(database='recommender.db', user=user_test_id, product=product_id, bundle_size=4, num_users=10, dinamic=0.1)
        d_recomendations.append(Recommender.main(dinamic_args))
        d_num_products += len(d_recomendations[-1])


    # For each recommended product, check if the user bought it in the
    # original database (checking if there is a review made by user of this product)
    sfp = 0
    stp = 0
    sbfp = 0
    sbtp = 0
    for bundle in s_recomendations:
        bundle_tp = False
        for recommended_prod in bundle:
            if Review.get_review_from_user_product(test.cursor, user_test_id, recommended_prod[0]):
                stp += 1
                if not bundle_tp:
                    sbtp += 1
                    bundle_tp = True
            else:
                sfp += 1
        if not bundle_tp:
            sbfp += 1

    dfp = 0
    dtp = 0
    dbfp = 0
    dbtp = 0
    for bundle in d_recomendations:
        bundle_tp = False
        for recommended_prod in bundle:
            if Review.get_review_from_user_product(test.cursor, user_test_id, recommended_prod[0]):
                dtp += 1
                if not bundle_tp:
                    dbtp += 1
                    bundle_tp = True
            else:
                dfp += 1
        if not bundle_tp:
            dbfp += 1

        results.update({
            user_test_id: {'sbtp': sbtp, 'sbfp': sbfp, 'stp': stp, 'sfp': sfp,
                           'dtp': dtp, 'dfp': dfp, 'dbtp': dbtp, 'dbfp': dbfp}
        })

outfile = open('out.csv', 'w')
outfile.write('user id,'
              '#static bundle recommendations,static bundle TP,static bundle FP,'
              '#static product recommendations,static products TP,static products FP,'
              '#dinamic bundle recommendations,dinamic bundle TP,dinamic bundle FP,'
              '#dinamic product recommendations,dinamic products TP,dinamic products FP\n')
for key in results:
    r = results[key]
    outfile.write('{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12}\n'
                  .format(key,
                          r['sbtp']+r['sbfp'], r['sbtp'], r['sbfp'],
                          r['stp']+r['sfp'], r['stp'], r['sfp'],
                          r['dbtp']+r['dbfp'], r['dbtp'], r['dbfp'],
                          r['dtp']+r['dfp'], r['dtp'], r['dfp']))
    print("\nUser {0}:".format(key))
    print("Static Recommendations\n   * Bundle True Positive: {0}\n   * Bundle False Positive: {1}\n"
          "   + Total Products True Positive: {2}\n   + Total Products False Positive: {3}".
          format(r['sbtp'], r['sbfp'], r['stp'], r['sfp']))

    print("Dinamic Recommendations\n   * Bundle True Positive: {0}\n   * Bundle False Positive: {1}\n"
          "   + Total Products True Positive: {2}\n   + Total Products False Positive: {3}\n\n".
          format(r['dbtp'], r['dbfp'], r['dtp'], r['dfp']))

outfile.close()
