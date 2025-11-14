from pydantic import BaseModel, ConfigDict


class CategoryIn(BaseModel):
    descr_tb_category: str


class CategoryOut(BaseModel):
    id_tb_category: int
    descr_tb_category: str
    model_config = ConfigDict(from_attributes=True)


class CategoryList(BaseModel):
    categories: list[CategoryOut]
