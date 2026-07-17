from sqlalchemy import (
    String, BigInteger, Numeric, Text, TIMESTAMP, Date, ForeignKey,
    Table, Column, UniqueConstraint, Boolean,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from ...db.session import Base


class AnimalGroup(Base):
    """Agrupación jerárquica libre (Arácnidos → Tarántulas, etc.)."""
    __tablename__ = "animal_groups"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("animal_groups.id", ondelete="RESTRICT"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    parent = relationship("AnimalGroup", remote_side=[id], back_populates="children")
    children = relationship("AnimalGroup", back_populates="parent")
    genera = relationship("Genus", back_populates="group")


class Genus(Base):
    __tablename__ = "genera"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    group_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("animal_groups.id", ondelete="RESTRICT"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    group = relationship("AnimalGroup", back_populates="genera")
    species = relationship("Species", back_populates="genus")


class Species(Base):
    __tablename__ = "species"
    __table_args__ = (UniqueConstraint("genus_id", "name", name="uq_species_genus_name"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    genus_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("genera.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    common_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    # Cómo se vende la especie: individual (folio único), package (de N) o colony (cepa)
    sale_format: Mapped[str] = mapped_column(String(20), nullable=False, server_default="individual")
    package_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    genus = relationship("Genus", back_populates="species")
    morphs = relationship("Morph", back_populates="species")
    animals = relationship("Animal", back_populates="species")


class Morph(Base):
    __tablename__ = "morphs"
    __table_args__ = (UniqueConstraint("species_id", "name", name="uq_morph_species_name"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    species_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("species.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    species = relationship("Species", back_populates="morphs")


animal_has_morphs = Table(
    "animal_has_morphs",
    Base.metadata,
    Column("animal_id", BigInteger, ForeignKey("animals.id", ondelete="CASCADE"), primary_key=True),
    Column("morph_id", BigInteger, ForeignKey("morphs.id", ondelete="CASCADE"), primary_key=True),
)


class AnimalPhoto(Base):
    __tablename__ = "animal_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    animal_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("animals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())


class Animal(Base):
    __tablename__ = "animals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    species_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("species.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Producto gemelo: el animal se vende por el POS a través de este producto
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, unique=True
    )

    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    # ponytail: enums como String + validación Pydantic; enum nativo de PG si algún día hace falta
    sex: Mapped[str] = mapped_column(String(10), nullable=False, server_default="unknown")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="available", index=True)

    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

    # Documentación legal (SEMARNAT/UMA); opcional — no todos los animales la requieren
    requires_legal_doc: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    legal_doc: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    legal_doc_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    species = relationship("Species", back_populates="animals")
    product = relationship("Product")
    morphs: Mapped[list["Morph"]] = relationship("Morph", secondary=animal_has_morphs)
    photos: Mapped[list["AnimalPhoto"]] = relationship(
        "AnimalPhoto", cascade="all, delete-orphan", order_by="AnimalPhoto.id"
    )
