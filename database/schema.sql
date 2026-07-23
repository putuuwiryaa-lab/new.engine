begin;

create table if not exists public.markets (
    id text primary key,
    name text not null,
    history_data text not null default '',
    "order" integer not null default 0,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists markets_order_idx
    on public.markets ("order");

alter table public.markets enable row level security;

revoke all on table public.markets from anon;
revoke all on table public.markets from authenticated;
grant all on table public.markets to service_role;

notify pgrst, 'reload schema';

commit;

-- Verifikasi setelah dijalankan:
-- select id, name, "order", updated_at
-- from public.markets
-- order by "order"
-- limit 10;
