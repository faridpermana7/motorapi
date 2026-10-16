from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from sqlalchemy.orm import selectinload
from model.admin.menu_model import MenuEntity, MenuDTO, MenuResponseDTO, MenuTreeDTO  
from model.admin.user_model import UserEntity  

class MenuRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _user_has_access_to_menu(self, user_id: Optional[int], menu: MenuEntity) -> bool:
        # If menu has no role restriction, it's public
        if menu.role_id is None:
            return True
            
        if not user_id:
            return False

        # Fetch user and their role details
        user_query = select(UserEntity).where(UserEntity.id == user_id).options(selectinload(UserEntity.role))
        user_res = await self.session.execute(user_query)
        user = user_res.scalars().first()

        if not user or not user.role_id:
            return False

        # Direct match with user's role_id
        if menu.role_id == user.role_id:
            return True

        # Check if menu's role_id is inside the user's role groups list (e.g. "2,3,4")
        if user.role and user.role.groups:
            group_ids = [int(g.strip()) for g in user.role.groups.split(",") if g.strip().isdigit()]
            if menu.role_id in group_ids:
                return True

        return False

    async def get_menu_tree(self, user_id: int) -> List[MenuTreeDTO]:
        query = (
            select(MenuEntity)
            .where(MenuEntity.deleted_at == None)
            .where(MenuEntity.is_active == True)
            .options(selectinload(MenuEntity.children), selectinload(MenuEntity.role))
            .order_by(MenuEntity.sort_order)
        )
        result = await self.session.execute(query)
        entities = result.scalars().all()

        # Filter entities based on user permissions synchronously/asynchronously
        async def build_tree(menu: MenuEntity) -> Optional[MenuTreeDTO]:
            if not await self._user_has_access_to_menu(user_id, menu):
                return None

            valid_children = []
            for child in menu.children:
                if child.deleted_at is None and child.is_active:
                    child_tree = await build_tree(child)
                    if child_tree:
                        valid_children.append(child_tree)

            return MenuTreeDTO(
                id=menu.id,
                label=menu.label,
                path=menu.path,
                icon=menu.icon,
                is_active=menu.is_active,
                sort_order=menu.sort_order,
                created_at=menu.created_at,
                created_by=menu.created_by,
                updated_at=menu.updated_at,
                updated_by=menu.updated_by,
                deleted_at=menu.deleted_at,
                children=valid_children
            )
        
        tree = []
        for m in entities:
            if m.parent_id is None and m.is_active:
                node = await build_tree(m)
                if node:
                    tree.append(node)
        return tree

    async def get_all_menus(self) -> List[MenuResponseDTO]:
        query = select(MenuEntity).where(MenuEntity.deleted_at == None).options(selectinload(MenuEntity.role))
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [MenuResponseDTO.from_orm(e) for e in entities]
    
    async def get_all_parents(self) -> List[MenuResponseDTO]:
        query = select(MenuEntity).where(MenuEntity.deleted_at == None, MenuEntity.parent_id == None).options(selectinload(MenuEntity.role))
        result = await self.session.execute(query)
        entities = result.scalars().all()
        return [MenuResponseDTO.from_orm(e) for e in entities]

    async def get_menu_by_id(self, menu_id: int) -> Optional[MenuResponseDTO]:
        query = (
            select(MenuEntity)
            .where(MenuEntity.deleted_at == None, MenuEntity.id == menu_id)
            .options(selectinload(MenuEntity.parent), selectinload(MenuEntity.role))
        )
        result = await self.session.execute(query)
        entity = result.scalars().first()
        return MenuResponseDTO.from_orm(entity) if entity else None
    
    async def update_menu(self, menu_id: int, data: MenuDTO, user: str) -> Optional[MenuResponseDTO]:
        query = select(MenuEntity).where(MenuEntity.deleted_at == None, MenuEntity.id == menu_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        if not entity:
            return None
        for key, value in data.dict(exclude={"children"}).items():
            setattr(entity, key, value)

        entity.updated_by = user
        entity.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(entity)
         
        return await self.get_menu_by_id(menu_id)

    async def create_menu(self, data: MenuDTO, user: str) -> Optional[MenuResponseDTO]:
        if data.parent_id:
            parent = await self.session.get(MenuEntity, data.parent_id)
            if not parent:
                raise ValueError(f"Parent menu {data.parent_id} does not exist")

        entity = MenuEntity(
            label=data.label,
            path=data.path,
            icon=data.icon,
            is_active=data.is_active,
            sort_order=data.sort_order,
            parent_id=data.parent_id,
            role_id=getattr(data, "role_id", None),
            created_by=user,
            created_at=datetime.utcnow()
        )
        self.session.add(entity)

        try:
            await self.session.commit()
            await self.session.refresh(entity)
        except Exception as e:
            await self.session.rollback()
            raise ValueError(str(e))

        return await self.get_menu_by_id(entity.id)
    
    async def delete_soft_menu(self, menu_id: int, user: str) -> bool:
        query = select(MenuEntity).where(MenuEntity.deleted_at == None, MenuEntity.id == menu_id)
        result = await self.session.execute(query)
        entity = result.scalars().first()
        if not entity:
            return False
        entity.deleted_at = datetime.utcnow()
        entity.updated_by = user
        await self.session.commit()
        await self.session.refresh(entity)
        return True

    async def delete_menu(self, menu_id: int) -> bool:
        result = await self.session.execute(select(MenuEntity).where(MenuEntity.id == menu_id))
        entity = result.scalars().first()
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

class MenuService:
    def __init__(self, repo: MenuRepository):
        self.repo = repo

    async def create_menu(self, data: MenuDTO, user: str) -> Optional[MenuResponseDTO]:
        return await self.repo.create_menu(data, user) 
    
    async def get_all_menus(self) -> List[MenuResponseDTO]:
        return await self.repo.get_all_menus()
    
    async def get_all_parents(self) -> List[MenuResponseDTO]:
        return await self.repo.get_all_parents()

    async def get_menu_tree(self, user_id: int) -> List[MenuTreeDTO]:
        return await self.repo.get_menu_tree(user_id)

    async def get_menu_by_id(self, menu_id: int) -> Optional[MenuResponseDTO]:
        return await self.repo.get_menu_by_id(menu_id)

    async def update_menu(self, menu_id: int, data: MenuDTO, user: str) -> Optional[MenuResponseDTO]:
        return await self.repo.update_menu(menu_id, data, user)

    async def delete_soft_menu(self, menu_id: int, user: str) -> bool:
        return await self.repo.delete_soft_menu(menu_id, user)

    async def delete_menu(self, menu_id: int) -> bool:
        return await self.repo.delete_menu(menu_id)