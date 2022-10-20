insert into role (
    id, name, description, version, org_id, uid,
    created, updated, display_name, group_name, hidden
) values (
    1, 'managed:builtins:viewer:permissions', '', 0, 1, 'SPRu-lSVz',
    datetime(), datetime(), '', '', 0
);

insert into builtin_role (
    id, role, role_id, created, updated, org_id
) values (
    1, 'Viewer', 1, datetime(), datetime(), 1
);
