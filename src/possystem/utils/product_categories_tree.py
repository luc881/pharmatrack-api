def build_category_tree(categories, parent_id=None):
    tree = []
    for cat in categories:
        if cat.parent_id == parent_id:
            node = {
                "id": cat.id,
                "name": cat.name,
                "image": cat.image,
                "is_active": cat.is_active,
                "parent_id": cat.parent_id,  # 👈 ADD THIS
                "children": build_category_tree(categories, cat.id)
            }
            tree.append(node)
    return tree




def serialize_category_tree(root, categories):
    root_dict = {
        "id": root.id,
        "name": root.name,
        "image": root.image,
        "is_active": root.is_active,
        "parent_id": root.parent_id,
        "children": build_category_tree(categories, root.id),
    }
    return root_dict


# def build_category_tree(categories, parent_id=None):
#     tree = []
#     for cat in categories:
#         if cat.parent_id == parent_id:
#             cat.children = build_category_tree(categories, cat.id)
#             tree.append(cat)
#     return tree