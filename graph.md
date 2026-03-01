graph TD
    %% 定义节点样式
    classDef definition fill:#e1f5fe,stroke:#0277bd,stroke-width:2px;
    classDef implementation fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef verification fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;

    %% 左侧：分解与定义过程 (Decomposition & Definition)
    subgraph "分解与定义 (向下)"
        A1[1. 用户需求与运行概念 (ConOps)<br>定义: 城市复杂场景ODD, 用户体验目标]:::definition
        A2[2. 系统需求定义 (SRD)<br>定义: 功能安全ASIL, 性能指标, 法规要求]:::definition
        A3[3. 系统架构设计 (SAD)<br>定义: 传感器布局, 计算平台, 软硬件接口, 冗余架构]:::definition
        A4[4. 子系统/模块设计 (MD)<br>定义: BEV感知, 预测模型, 规控算法, 高精地图引擎]:::definition
    end

    %% 底部：实现过程 (Implementation)
    subgraph "实现 (底部)"
        B[5. 软硬件实现与编码<br>行动: 代码编写, 模型训练, 硬件制板]:::implementation
    end

    %% 右侧：集成与验证过程 (Integration & Verification)
    subgraph "集成与验证 (向上)"
        C4[6. 模块/单元测试 (Unit Test)<br>验证: 算法SIL测试, 模型精度验证]:::verification
        C3[7. 子系统集成与验证 (Subsys V&V)<br>验证: 软件在环SIL, 处理器在环PIL, 联合仿真]:::verification
        C2[8. 系统集成与验证 (System V&V)<br>验证: 硬件在环HIL, 整车在环VIL, 封闭场地测试, 故障注入]:::verification
        C1[9. 系统确认与验收 (Validation)<br>确认: 大规模开放道路测试, Beta用户试驾, 法规认证, OTA部署]:::verification
    end

    %% 定义连接关系 (V字形流向)
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> B
    B --> C4
    C4 --> C3
    C3 --> C2
    C2 --> C1

    %% 定义水平验证关系 (V&V Linkage)
    A4 -.->|验证设计满足需求| C4
    A3 -.->|验证架构合理性| C3
    A2 -.->|验证系统满足系统需求| C2
    A1 -.->|确认系统满足用户需求| C1

    %% 添加说明标题
    style A1 text-align:center
    style C1 text-align:center