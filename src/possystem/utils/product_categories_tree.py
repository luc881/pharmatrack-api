def build_category_tree(categories, parent_id=None):
    tree = []
    for cat in categories:
        if cat.parent_id == parent_id:
            children = build_category_tree(categories, cat.id)
            cat.children = children
            tree.append(cat)
    return tree


# def build_category_tree(categories, parent_id=None):
#     tree = []
#     for cat in categories:
#         if cat.parent_id == parent_id:
#             cat.children = build_category_tree(categories, cat.id)
#             tree.append(cat)
#     return tree