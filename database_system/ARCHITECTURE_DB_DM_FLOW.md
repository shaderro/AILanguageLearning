## 数据库与 Data Manager 转换时机与分工流程图

> 说明：以下为从请求进入到数据库读写返回的完整链路，以及各层分工与模型/DTO转换时机。可在支持 Mermaid 的查看器中直接渲染。

### 序列图：请求到数据库的完整链路与转换时机

```mermaid
sequenceDiagram
    autonumber
    participant C as Client(Frontend)
    participant A as FastAPI Route
    participant S as Session(per-request)
    participant DM as DataManagers(backed by DB, returns DTO)
    participant AD as Adapters(models↔DTO)
    participant M as Managers(业务编排)
    participant DAL as DAL(聚合CRUD)
    participant CRUD as CRUD(最小读写)
    participant DB as Database(Models)

    C->>A: 发起请求(REST/JSON)
    A->>S: 依赖注入获取 Session
    A->>DM: 调用领域接口(入参=DTO/原始参数)
    DM->>AD: DTO→(必要时)Models 字段规范化/校验
    DM->>M: 调用业务编排（传 Session）
    M->>DAL: 组合查询/写入步骤（传 Session）
    DAL->>CRUD: 执行原子级 DB 操作（传 Session）
    CRUD->>DB: 查询/INSERT/UPDATE/DELETE(ORM Models)
    DB-->>CRUD: 结果(Models)
    CRUD-->>DAL: 返回(Models)
    DAL-->>M: 返回(Models)
    M-->>DM: 返回(Models)
    DM->>AD: Models→DTO 映射、字段过滤
    AD-->>DM: 返回 DTO
    alt 成功
        DM->>S: commit()
        S-->>A: 返回 DTO
        A-->>C: 200 OK + JSON(DTO)
    else 出错
        DM->>S: rollback()
        A-->>C: 标准化错误(Validation/NotFound/Conflict)
    end
```

### 分层与分工：谁负责什么、在哪里转换

```mermaid
graph TD
    subgraph API层
        R[FastAPI Routes<br/>- 依赖注入 Session<br/>- 输入校验/鉴权<br/>- 错误映射]
    end

    subgraph 领域编排层(后端AI逻辑)
        DM[backend/data/data_managers<br/>- 统一对外DTO接口<br/>- 仅接触DTO]
        AD[adapters orm↔dto<br/>- 字段映射/规范化<br/>- 枚举/时间戳处理]
    end

    subgraph 数据库业务层
        M[Managers<br/>- 业务编排/事务边界建议位]
        DAL[Data Access Layer<br/>- 聚合多步CRUD]
        CRUD[CRUD<br/>- 原子级SQL/ORM]
    end

    subgraph 存储层
        MOD[Models(SQLAlchemy)]
        DB[(Database)]
    end

    R --> DM
    DM <---> AD
    DM --> M
    M --> DAL --> CRUD --> MOD --> DB
    MOD -. 映射 .- AD
```

关键说明：

- DTO→Models：进入数据库业务层前在 `adapters` 进行字段规范化与枚举转换。
- Models→DTO：从数据库层返回后在 `adapters` 统一输出，保证对上层形态稳定。
- 事务边界：每请求一个 Session；写操作完成后统一 `commit/rollback`，通常由路由或统一数据管理器封装。
- 错误策略：将底层 DB/ORM 异常映射为业务错误（Validation/NotFound/Conflict）。


