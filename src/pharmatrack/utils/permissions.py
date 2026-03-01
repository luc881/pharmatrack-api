from fastapi import Depends
from ..utils.security import require_permission


# Permissions for user operations
CAN_READ_USERS = [Depends(require_permission("users.read"))]
CAN_CREATE_USERS = [Depends(require_permission("users.create"))]
CAN_UPDATE_USERS = [Depends(require_permission("users.update"))]
CAN_DELETE_USERS = [Depends(require_permission("users.delete"))]

# Permissions for branch operations
CAN_READ_BRANCHES = [Depends(require_permission("branches.read"))]
CAN_CREATE_BRANCHES = [Depends(require_permission("branches.create"))]
CAN_UPDATE_BRANCHES = [Depends(require_permission("branches.update"))]
CAN_DELETE_BRANCHES = [Depends(require_permission("branches.delete"))]

# Permissions for permission operations
CAN_READ_PERMISSIONS = [Depends(require_permission("permissions.read"))]
CAN_CREATE_PERMISSIONS = [Depends(require_permission("permissions.create"))]
CAN_UPDATE_PERMISSIONS = [Depends(require_permission("permissions.update"))]
CAN_DELETE_PERMISSIONS = [Depends(require_permission("permissions.delete"))]

# Permissions for role operations
CAN_READ_ROLES = [Depends(require_permission("roles.read"))]
CAN_CREATE_ROLES = [Depends(require_permission("roles.create"))]
CAN_UPDATE_ROLES = [Depends(require_permission("roles.update"))]
CAN_DELETE_ROLES = [Depends(require_permission("roles.delete"))]

# Permissions for product operations
CAN_READ_PRODUCTS = [Depends(require_permission("products.read"))]
CAN_CREATE_PRODUCTS = [Depends(require_permission("products.create"))]
CAN_UPDATE_PRODUCTS = [Depends(require_permission("products.update"))]
CAN_DELETE_PRODUCTS = [Depends(require_permission("products.delete"))]

# Permissions for product category operations
CAN_READ_PRODUCT_CATEGORIES = [Depends(require_permission("productscategories.read"))]
CAN_CREATE_PRODUCT_CATEGORIES = [Depends(require_permission("productscategories.create"))]
CAN_UPDATE_PRODUCT_CATEGORIES = [Depends(require_permission("productscategories.update"))]
CAN_DELETE_PRODUCT_CATEGORIES = [Depends(require_permission("productscategories.delete"))]

# Permissions for sales operations
CAN_READ_SALES = [Depends(require_permission("sales.read"))]
CAN_CREATE_SALES = [Depends(require_permission("sales.create"))]
CAN_UPDATE_SALES = [Depends(require_permission("sales.update"))]
CAN_DELETE_SALES = [Depends(require_permission("sales.delete"))]

# Permissions for sale payment operations
CAN_READ_SALE_PAYMENTS = [Depends(require_permission("salepayments.read"))]
CAN_CREATE_SALE_PAYMENTS = [Depends(require_permission("salepayments.create"))]
CAN_UPDATE_SALE_PAYMENTS = [Depends(require_permission("salepayments.update"))]
CAN_DELETE_SALE_PAYMENTS = [Depends(require_permission("salepayments.delete"))]

# Permissions for sale detail operations
CAN_READ_SALE_DETAILS = [Depends(require_permission("saledetails.read"))]
CAN_CREATE_SALE_DETAILS = [Depends(require_permission("saledetails.create"))]
CAN_UPDATE_SALE_DETAILS = [Depends(require_permission("saledetails.update"))]
CAN_DELETE_SALE_DETAILS = [Depends(require_permission("saledetails.delete"))]

# Permissions for refund product operations
CAN_READ_REFUND_PRODUCTS = [Depends(require_permission("refundproducts.read"))]
CAN_CREATE_REFUND_PRODUCTS = [Depends(require_permission("refundproducts.create"))]
CAN_UPDATE_REFUND_PRODUCTS = [Depends(require_permission("refundproducts.update"))]
CAN_DELETE_REFUND_PRODUCTS = [Depends(require_permission("refundproducts.delete"))]

# Permissions for supplier operations
CAN_READ_SUPPLIERS = [Depends(require_permission("suppliers.read"))]
CAN_CREATE_SUPPLIERS = [Depends(require_permission("suppliers.create"))]
CAN_UPDATE_SUPPLIERS = [Depends(require_permission("suppliers.update"))]
CAN_DELETE_SUPPLIERS = [Depends(require_permission("suppliers.delete"))]

# Permissions for purchase operations
CAN_READ_PURCHASES = [Depends(require_permission("purchases.read"))]
CAN_CREATE_PURCHASES = [Depends(require_permission("purchases.create"))]
CAN_UPDATE_PURCHASES = [Depends(require_permission("purchases.update"))]
CAN_DELETE_PURCHASES = [Depends(require_permission("purchases.delete"))]

# Permissions for purchase detail operations
CAN_READ_PURCHASE_DETAILS = [Depends(require_permission("purchasedetails.read"))]
CAN_CREATE_PURCHASE_DETAILS = [Depends(require_permission("purchasedetails.create"))]
CAN_UPDATE_PURCHASE_DETAILS = [Depends(require_permission("purchasedetails.update"))]
CAN_DELETE_PURCHASE_DETAILS = [Depends(require_permission("purchasedetails.delete"))]

# Permissions for product batch operations
CAN_READ_PRODUCT_BATCHES = [Depends(require_permission("productbatches.read"))]
CAN_CREATE_PRODUCT_BATCHES = [Depends(require_permission("productbatches.create"))]
CAN_UPDATE_PRODUCT_BATCHES = [Depends(require_permission("productbatches.update"))]
CAN_DELETE_PRODUCT_BATCHES = [Depends(require_permission("productbatches.delete"))]

# Permissions for sale batch usage operations
CAN_READ_SALE_BATCH_USAGES = [Depends(require_permission("salebatchusages.read"))]
CAN_CREATE_SALE_BATCH_USAGES = [Depends(require_permission("salebatchusages.create"))]
CAN_UPDATE_SALE_BATCH_USAGES = [Depends(require_permission("salebatchusages.update"))]
CAN_DELETE_SALE_BATCH_USAGES = [Depends(require_permission("salebatchusages.delete"))]

# Permissions for product master operations
CAN_READ_PRODUCT_MASTERS = [Depends(require_permission("productmasters.read"))]
CAN_CREATE_PRODUCT_MASTERS = [Depends(require_permission("productmasters.create"))]
CAN_UPDATE_PRODUCT_MASTERS = [Depends(require_permission("productmasters.update"))]
CAN_DELETE_PRODUCT_MASTERS = [Depends(require_permission("productmasters.delete"))]

# Permissions for product brand operations
CAN_READ_PRODUCT_BRANDS = [Depends(require_permission("productbrands.read"))]
CAN_CREATE_PRODUCT_BRANDS = [Depends(require_permission("productbrands.create"))]
CAN_UPDATE_PRODUCT_BRANDS = [Depends(require_permission("productbrands.update"))]
CAN_DELETE_PRODUCT_BRANDS = [Depends(require_permission("productbrands.delete"))]

# Permissions for ingredient operations
CAN_READ_INGREDIENTS = [Depends(require_permission("ingredients.read"))]
CAN_CREATE_INGREDIENTS = [Depends(require_permission("ingredients.create"))]
CAN_UPDATE_INGREDIENTS = [Depends(require_permission("ingredients.update"))]
CAN_DELETE_INGREDIENTS = [Depends(require_permission("ingredients.delete"))]

# Permissions for unit operations
# CAN_READ_UNITS = [Depends(require_permission("units.read"))]
# CAN_CREATE_UNITS = [Depends(require_permission("units.create"))]
# CAN_UPDATE_UNITS = [Depends(require_permission("units.update"))]
# CAN_DELETE_UNITS = [Depends(require_permission("units.delete"))]

# Permissions for warehouse operations
# CAN_READ_WAREHOUSES = [Depends(require_permission("warehouses.read"))]
# CAN_CREATE_WAREHOUSES = [Depends(require_permission("warehouses.create"))]
# CAN_UPDATE_WAREHOUSES = [Depends(require_permission("warehouses.update"))]
# CAN_DELETE_WAREHOUSES = [Depends(require_permission("warehouses.delete"))]

# Permissions for product warehouse operations
# CAN_READ_PRODUCT_WAREHOUSES = [Depends(require_permission("productwarehouses.read"))]
# CAN_CREATE_PRODUCT_WAREHOUSES = [Depends(require_permission("productwarehouses.create"))]
# CAN_UPDATE_PRODUCT_WAREHOUSES = [Depends(require_permission("productwarehouses.update"))]
# CAN_DELETE_PRODUCT_WAREHOUSES = [Depends(require_permission("productwarehouses.delete"))]

# Permissions for product wallet operations
# CAN_READ_PRODUCT_WALLETS = [Depends(require_permission("productwallets.read"))]
# CAN_CREATE_PRODUCT_WALLETS = [Depends(require_permission("productwallets.create"))]
# CAN_UPDATE_PRODUCT_WALLETS = [Depends(require_permission("productwallets.update"))]
# CAN_DELETE_PRODUCT_WALLETS = [Depends(require_permission("productwallets.delete"))]

# Permissions for product stock initial operations
# CAN_READ_PRODUCT_STOCK_INITIALS = [Depends(require_permission("productstockinitials.read"))]
# CAN_CREATE_PRODUCT_STOCK_INITIALS = [Depends(require_permission("productstockinitials.create"))]
# CAN_UPDATE_PRODUCT_STOCK_INITIALS = [Depends(require_permission("productstockinitials.update"))]
# CAN_DELETE_PRODUCT_STOCK_INITIALS = [Depends(require_permission("productstockinitials.delete"))]

# Permissions for client operations
# CAN_READ_CLIENTS = [Depends(require_permission("clients.read"))]
# CAN_CREATE_CLIENTS = [Depends(require_permission("clients.create"))]
# CAN_UPDATE_CLIENTS = [Depends(require_permission("clients.update"))]
# CAN_DELETE_CLIENTS = [Depends(require_permission("clients.delete"))]

# Permissions for sale detail attention operations
# CAN_READ_SALE_DETAIL_ATTENTIONS = [Depends(require_permission("saledetailattentions.read"))]
# CAN_CREATE_SALE_DETAIL_ATTENTIONS = [Depends(require_permission("saledetailattentions.create"))]
# CAN_UPDATE_SALE_DETAIL_ATTENTIONS = [Depends(require_permission("saledetailattentions.update"))]
# CAN_DELETE_SALE_DETAIL_ATTENTIONS = [Depends(require_permission("saledetailattentions.delete"))]

# Permissions for transport operations
# CAN_READ_TRANSPORTS = [Depends(require_permission("transports.read"))]
# CAN_CREATE_TRANSPORTS = [Depends(require_permission("transports.create"))]
# CAN_UPDATE_TRANSPORTS = [Depends(require_permission("transports.update"))]
# CAN_DELETE_TRANSPORTS = [Depends(require_permission("transports.delete"))]

# Permissions for conversion operations
# CAN_READ_CONVERSIONS = [Depends(require_permission("conversions.read"))]
# CAN_CREATE_CONVERSIONS = [Depends(require_permission("conversions.create"))]
# CAN_UPDATE_CONVERSIONS = [Depends(require_permission("conversions.update"))]
# CAN_DELETE_CONVERSIONS = [Depends(require_permission("conversions.delete"))]




