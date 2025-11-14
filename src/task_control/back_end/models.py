from sqlalchemy.orm import Mapped, mapped_column, registry

table_registry = registry()


@table_registry.mapped_as_dataclass
class Category:
    __tablename__ = 'tb_category'

    id_tb_category: Mapped[int] = mapped_column(init=False, primary_key=True)
    descr_tb_category: Mapped[str] = mapped_column(unique=True)
