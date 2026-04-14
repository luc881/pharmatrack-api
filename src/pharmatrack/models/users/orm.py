from sqlalchemy import String, BigInteger, SmallInteger, TIMESTAMP, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.sql import func
from ...db.session import Base
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pharmatrack.types.users import GenderEnum, DocumentTypeEnum

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    surname: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email_verified_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    remember_token: Mapped[str] = mapped_column(String(100), nullable=True)
    refresh_token_expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now())
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("roles.id"), nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("branches.id"), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    type_document: Mapped[DocumentTypeEnum] = mapped_column(
        SAEnum(DocumentTypeEnum, name="documenttypeenum", create_type=False,
               values_callable=lambda x: [e.value for e in x]), nullable=True
    )
    n_document: Mapped[str] = mapped_column(String(50), nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    gender: Mapped[GenderEnum] = mapped_column(
        SAEnum(GenderEnum, name="genderenum", create_type=False,
               values_callable=lambda x: [e.value for e in x]), nullable=True
    )

    # Relationship to Role
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="selectin")
    branch: Mapped["Branch"] = relationship("Branch", back_populates="users", lazy="selectin")
    # clients: Mapped[list["Client"]] = relationship("Client", back_populates="user")
    sales: Mapped[list["Sale"]] = relationship("Sale", back_populates="user")
    refund_products: Mapped[list["RefundProduct"]] = relationship("RefundProduct", back_populates="user")
    purchases = relationship("Purchase", back_populates="user")
    # transports: Mapped[list["Transport"]] = relationship("Transport", back_populates="user")
    # delivered_purchase_details = relationship(
    #     "PurchaseDetail",
    #     back_populates="user",
    #     foreign_keys="[PurchaseDetail.user_entrega]"
    # )
    # delivered_transport_details: Mapped[list["TransportDetail"]] = relationship(
    #     "TransportDetail",
    #     back_populates="user_delivery",
    #     foreign_keys="[TransportDetail.user_delivery_id]"
    # )
    # departed_transport_details: Mapped[list["TransportDetail"]] = relationship(
    #     "TransportDetail",
    #     back_populates="user_departure",
    #     foreign_keys="[TransportDetail.user_departure_id]"
    # )
    # conversions: Mapped[list["Conversion"]] = relationship(
    #     "Conversion", back_populates="user"
    # )
