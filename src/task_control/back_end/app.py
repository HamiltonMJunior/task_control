from http import HTTPStatus

from database import get_session
from fastapi import Depends, FastAPI, HTTPException
from models import Category
from schemas import CategoryList, CategoryIn, CategoryOut
from sqlalchemy import select
from sqlalchemy.orm import Session

app = FastAPI()


@app.get('/')
def read_root():
    return {'mensagem': 'Hello World!'}


#Categorias================================================================================
@app.get('/category/', status_code=HTTPStatus.OK, response_model=CategoryList)
def list_category(session: Session = Depends(get_session)):
    category = session.scalars(select(Category)).all()

    return CategoryList(categories=category)


@app.post('/category/', status_code=HTTPStatus.CREATED, response_model=CategoryOut)
def create_category(category: CategoryIn, session: Session = Depends(get_session)):
    db_category = session.scalar(
        select(Category).where(
            Category.descr_tb_category == category.descr_tb_category
        )
    )

    if db_category:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Category already exists'
        )
    
    db_category = Category(category.descr_tb_category)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)

    return db_category