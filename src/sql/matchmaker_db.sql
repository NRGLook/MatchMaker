-- Таблица категорий событий
CREATE TABLE CATEGORY (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255)
);

-- Таблица пользователей
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    age INT CHECK (age > 0), -- Ограничение на возраст
    experience INT CHECK (experience >= 0), -- Ограничение на опыт
    created_at DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Таблица команд
CREATE TABLE TEAM (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    logo_url VARCHAR(255)
);

-- Таблица событий
CREATE TABLE EVENT (
    id SERIAL PRIMARY KEY,
    category_id INT NOT NULL,
    location GEOGRAPHY,
    people_amount INT CHECK (people_amount >= 0), -- Ограничение на количество участников
    experience INT CHECK (experience >= 0), -- Минимальный опыт участников
    date_time DATE NOT NULL,
    organizer_id INT NOT NULL,
    description VARCHAR(255),
    CONSTRAINT fk_category FOREIGN KEY (category_id) REFERENCES CATEGORY (id) ON DELETE CASCADE,
    CONSTRAINT fk_organizer FOREIGN KEY (organizer_id) REFERENCES "user" (id) ON DELETE SET NULL
);

-- Таблица RSVP (участие в событиях)
CREATE TABLE RSVP (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    status VARCHAR(50) CHECK (status IN ('accepted', 'declined', 'pending')), -- Допустимые значения
    responded_at DATE,
    CONSTRAINT fk_user_rsvp FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE,
    CONSTRAINT fk_event_rsvp FOREIGN KEY (event_id) REFERENCES EVENT (id) ON DELETE CASCADE
);

-- Таблица игроков
CREATE TABLE PLAYER (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    rsvp_id INT NOT NULL,
    team_id INT,
    CONSTRAINT fk_user_player FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE,
    CONSTRAINT fk_rsvp_player FOREIGN KEY (rsvp_id) REFERENCES RSVP (id) ON DELETE CASCADE,
    CONSTRAINT fk_team_player FOREIGN KEY (team_id) REFERENCES TEAM (id) ON DELETE SET NULL
);

-- Таблица статистики
CREATE TABLE STATISTIC (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    score INT CHECK (score >= 0), -- Ограничение на очки
    rating DOUBLE PRECISION CHECK (rating >= 0 AND rating <= 5), -- Ограничение на рейтинг
    updated_at DATE NOT NULL DEFAULT CURRENT_DATE,
    CONSTRAINT fk_user_statistic FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE,
    CONSTRAINT fk_event_statistic FOREIGN KEY (event_id) REFERENCES EVENT (id) ON DELETE CASCADE
);
