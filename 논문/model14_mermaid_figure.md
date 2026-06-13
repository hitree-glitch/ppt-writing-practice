# Figure. Generativity-Moderated Indirect Association From Grief to Suicide Risk

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#ffffff",
    "primaryColor": "#f7f7f5",
    "primaryTextColor": "#202124",
    "primaryBorderColor": "#4b5563",
    "lineColor": "#374151",
    "secondaryColor": "#eef2f7",
    "tertiaryColor": "#fff7ed",
    "fontFamily": "Arial, sans-serif"
  }
}}%%
flowchart LR
    G["사별 고통<br/>(GriefTot)"]
    P["PTSD 증상<br/>(PCLTot)"]
    S["자살위험<br/>(SBQTot)"]
    L["생성감<br/>(LGS_Tot)"]
    I["상호작용항<br/>(PCLTot × LGS_Tot)"]

    G -->|"a 경로"| P
    P -->|"b 경로"| S
    G -.->|"c' 직접경로"| S
    P --> I
    L --> I
    I -.->|"조절효과"| S

    classDef exposure fill:#f8fafc,stroke:#334155,stroke-width:1.4px,color:#111827;
    classDef mediator fill:#eef2ff,stroke:#4338ca,stroke-width:1.4px,color:#111827;
    classDef outcome fill:#fff1f2,stroke:#be123c,stroke-width:1.4px,color:#111827;
    classDef moderator fill:#ecfdf5,stroke:#047857,stroke-width:1.4px,color:#111827;
    classDef interaction fill:#ffffff,stroke:#6b7280,stroke-width:1.2px,stroke-dasharray:4 3,color:#111827;

    class G exposure;
    class P mediator;
    class S outcome;
    class L moderator;
    class I interaction;
```

Note. The model represents a cross-sectional moderated indirect association. Grief severity was indirectly associated with suicide risk through PTSD symptoms. This indirect association was evident at low and average levels of generativity, but not at high levels of generativity.
