create table player (
    id integer primary key,
    first_name varchar(20) not null,
    last_name varchar(20) not null,
    birth_date date not null,
    bat_side varchar(1) not null,
    throw_arm varchar(1) not null
)

create table team (
    id integer primary key,
    name varchar(20) not null,
    year integer not null
)

create table player_team (
    player_id integer not null,
    team_id integer not null,
    foreign key (player_id) references player(id),
    foreign key (team_id) references team(id)
)

create table position (
    id integer primary key,
    position varchar(20) not null
)

create table player_position (
    player_id integer not null,
    position_id integer not null,
    foreign key (player_id) references player(id),
    foreign key (position_id) references position(id)
)

create table pitching_stats (
    player_id integer not null,
    year integer not null,
    era decimal(3,2) not null,
    innings_pitched decimal(3,1) not null,
    wins integer not null,
    losses integer not null,
    strikeouts integer not null,
    foreign key (player_id) references player(id)
)

create table batting_stats (
    player_id integer not null,
    year integer not null,
    batting_average decimal(1,3) not null,
    at_bats integer not null,
    hits integer not null,
    home_runs integer not null,
    foreign key (player_id) references player(id)
)

create table awards (
    id integer primary key,
    player_id integer not null,
    award_name varchar(50) not null,
    year integer not null
)