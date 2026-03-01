from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from ..models.product_categories.orm import ProductCategory


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

def check_category_cycle(db, category_id: int, new_parent_id: int):
    """
    Prevent cyclic category relationships
    """
    current_parent_id = new_parent_id

    while current_parent_id is not None:
        if current_parent_id == category_id:
            raise HTTPException(
                status_code=400,
                detail="Category cycle detected"
            )

        parent = db.get(ProductCategory, current_parent_id)
        if not parent:
            break

        current_parent_id = parent.parent_id




# def build_category_tree(categories, parent_id=None):
#     tree = []
#     for cat in categories:
#         if cat.parent_id == parent_id:
#             cat.children = build_category_tree(categories, cat.id)
#             tree.append(cat)
#     return tree