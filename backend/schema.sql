create table if not exists organizations (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  plan        text not null default 'free',
  created_at  timestamptz not null default now()
);

create table if not exists api_keys (
  id          uuid primary key default gen_random_uuid(),
  org_id      uuid not null references organizations(id) on delete cascade,
  name        text not null,
  key_hash    text not null unique,
  key_prefix  text not null,
  is_active   boolean not null default true,
  last_used   timestamptz,
  created_at  timestamptz not null default now()
);
create index if not exists api_keys_key_hash_idx on api_keys(key_hash);
create index if not exists api_keys_org_idx on api_keys(org_id);

create table if not exists agents (
  id          uuid primary key default gen_random_uuid(),
  org_id      uuid not null references organizations(id) on delete cascade,
  name        text not null,
  description text,
  framework   text,
  metadata    jsonb not null default '{}',
  last_active timestamptz,
  created_at  timestamptz not null default now()
);
create index if not exists agents_org_idx on agents(org_id);

create table if not exists memories (
  id           uuid primary key default gen_random_uuid(),
  org_id       uuid not null references organizations(id) on delete cascade,
  agent_id     text not null,
  input        jsonb not null,
  output       jsonb not null,
  memory_type  text not null default 'episodic',
  outcome      text not null default 'pending',
  metadata     jsonb not null default '{}',
  tags         text[] not null default '{}',
  tool_calls   jsonb not null default '[]',
  latency_ms   integer,
  tokens_used  integer,
  created_at   timestamptz not null default now()
);
create index if not exists memories_org_idx on memories(org_id);
create index if not exists memories_agent_idx on memories(org_id, agent_id);
create index if not exists memories_outcome_idx on memories(org_id, outcome);
create index if not exists memories_created_idx on memories(org_id, created_at desc);

alter table organizations enable row level security;
alter table api_keys enable row level security;
alter table agents enable row level security;
alter table memories enable row level security;
