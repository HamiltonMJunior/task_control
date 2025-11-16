from http import HTTPStatus

from database import get_session
from fastapi import Depends, FastAPI, HTTPException
from models import Category
from schemas import CategoryIn, CategoryList, CategoryOut
from sqlalchemy import select
from sqlalchemy.orm import Session

app = FastAPI()


@app.get('/')
def read_root():
    return {'mensagem': 'Hello World!'}


# Categorias===================================================================
@app.get('/category/', status_code=HTTPStatus.OK, response_model=CategoryList)
def list_category(session: Session = Depends(get_session)):
    category = session.scalars(select(Category)).all()

    return CategoryList(categories=category)


@app.post(
    '/category/', status_code=HTTPStatus.CREATED, response_model=CategoryOut
)
def create_category(
    category: CategoryIn, session: Session = Depends(get_session)
):
    db_category = session.scalar(
        select(Category).where(
            Category.descr_tb_category == category.descr_tb_category
        )
    )

    if db_category:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Category already exists'
        )

    db_category = Category(category.descr_tb_category)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)

    return db_category


@app.delete('/category/{category_id}', status_code=HTTPStatus.NO_CONTENT)
def delete_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Category not found',
        )

    session.delete(category)
    session.commit()


@app.put('/category/{category_id}', response_model=CategoryOut)
def update_category(
    category_id: int,
    category_in: CategoryIn,
    session: Session = Depends(get_session),
):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Category not found',
        )

    existing = session.scalar(
        select(Category).where(
            Category.descr_tb_category == category_in.descr_tb_category,
            Category.id_tb_category != category_id,
        )
    )
    if existing:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Another category with this description already exists',
        )

    category.descr_tb_category = category_in.descr_tb_category
    session.commit()
    session.refresh(category)
    return category
