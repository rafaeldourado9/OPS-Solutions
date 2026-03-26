from uuid import UUID

from fastapi import Depends

from adapters.inbound.api.middleware.auth import CurrentUser, get_current_user


async def get_tenant_id(user: CurrentUser = Depends(get_current_user)) -> UUID:
    return user.tenant_id
