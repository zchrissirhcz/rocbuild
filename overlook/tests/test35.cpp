#include <stdio.h>

class Entity
{
public:
    Entity()
    {
        printf("Entity ctor()\n");
    }
    ~Entity()
    {
        printf("Entity dtor()\n");
    }

    virtual void hello() const
    {
        printf("Entity::hello()\n");
    }
};

class SubEntity : public Entity
{
public:
    void hello() const
    {
        printf("SubEntity::hello()\n");
    }
    SubEntity()
    {
        printf("SubEntity ctor()\n");
    }
    ~SubEntity()
    {
        printf("SubEntity dtor()\n");
    }
};

int main()
{
    printf("hello cmake\n");

    // SubEntity entity;
    // entity.hello();

    Entity* p = new SubEntity;
    p->hello();
    delete p; // 实际上，如果(在Linux）开启了 clangd， 例如 VSCode + clangd 插件， 会直接提示为下划波浪线

    return 0;
}
