--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'Standard public schema';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: games; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE games (
    id serial NOT NULL,
    server smallint,
    "start" timestamp without time zone DEFAULT now()
);


ALTER TABLE public.games OWNER TO postgres;

--
-- Name: games_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('games', 'id'), 24, true);


--
-- Name: openttd_versions; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE openttd_versions (
    id serial NOT NULL,
    version character varying(32)
);


ALTER TABLE public.openttd_versions OWNER TO postgres;

--
-- Name: openttd_versions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('openttd_versions', 'id'), 3, true);


--
-- Name: servers; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE servers (
    id serial NOT NULL,
    "owner" integer,
    name character varying(30),
    port smallint,
    status character varying(10) DEFAULT 'offline'::character varying,
    enabled boolean DEFAULT false,
    advertise boolean DEFAULT true,
    "password" character varying(32),
    version integer,
    config_changed timestamp without time zone,
    config_applied timestamp without time zone,
    url character varying(15) NOT NULL,
    descr text,
    CONSTRAINT valid_url CHECK (((url)::text ~* '^[[:alnum:]_.-]*$'::text))
);


ALTER TABLE public.servers OWNER TO postgres;

--
-- Name: servers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('servers', 'id'), 53, true);


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE users (
    id serial NOT NULL,
    username character varying(20) NOT NULL,
    "password" character(32) NOT NULL,
    signup_at timestamp with time zone,
    CONSTRAINT username_valid_dns CHECK (((username)::text ~* '^[[:alnum:]-]+$'::text)),
    CONSTRAINT username_valid_dns_negative CHECK (((username)::text !~* '^-|--|-$'::text))
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval(pg_catalog.pg_get_serial_sequence('users', 'id'), 35, true);


--
-- Name: valid_ports; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW valid_ports AS
    SELECT port.port FROM generate_series(7100, 7200) port(port);


ALTER TABLE public.valid_ports OWNER TO postgres;

--
-- Name: games_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY games
    ADD CONSTRAINT games_pkey PRIMARY KEY (id);


--
-- Name: openttd_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY openttd_versions
    ADD CONSTRAINT openttd_versions_pkey PRIMARY KEY (id);


--
-- Name: servers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY servers
    ADD CONSTRAINT servers_pkey PRIMARY KEY (id);


--
-- Name: servers_port_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY servers
    ADD CONSTRAINT servers_port_key UNIQUE (port);


--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: unique_owner_url; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE UNIQUE INDEX unique_owner_url ON servers USING btree ("owner", url);


--
-- Name: games_server_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY games
    ADD CONSTRAINT games_server_fkey FOREIGN KEY (server) REFERENCES servers(id);


--
-- Name: servers_owner_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY servers
    ADD CONSTRAINT servers_owner_fkey FOREIGN KEY ("owner") REFERENCES users(id);


--
-- Name: servers_version_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY servers
    ADD CONSTRAINT servers_version_fkey FOREIGN KEY (version) REFERENCES openttd_versions(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: games; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE games FROM PUBLIC;
REVOKE ALL ON TABLE games FROM postgres;
GRANT ALL ON TABLE games TO postgres;
GRANT ALL ON TABLE games TO my_ottd;


--
-- Name: games_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE games_id_seq FROM PUBLIC;
REVOKE ALL ON TABLE games_id_seq FROM postgres;
GRANT ALL ON TABLE games_id_seq TO postgres;
GRANT ALL ON TABLE games_id_seq TO my_ottd;


--
-- Name: openttd_versions; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE openttd_versions FROM PUBLIC;
REVOKE ALL ON TABLE openttd_versions FROM postgres;
GRANT ALL ON TABLE openttd_versions TO postgres;
GRANT ALL ON TABLE openttd_versions TO my_ottd;


--
-- Name: openttd_versions_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE openttd_versions_id_seq FROM PUBLIC;
REVOKE ALL ON TABLE openttd_versions_id_seq FROM postgres;
GRANT ALL ON TABLE openttd_versions_id_seq TO postgres;
GRANT ALL ON TABLE openttd_versions_id_seq TO my_ottd;


--
-- Name: servers; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE servers FROM PUBLIC;
REVOKE ALL ON TABLE servers FROM postgres;
GRANT ALL ON TABLE servers TO postgres;
GRANT ALL ON TABLE servers TO my_ottd;


--
-- Name: servers_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE servers_id_seq FROM PUBLIC;
REVOKE ALL ON TABLE servers_id_seq FROM postgres;
GRANT ALL ON TABLE servers_id_seq TO postgres;
GRANT ALL ON TABLE servers_id_seq TO my_ottd;


--
-- Name: users; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE users FROM PUBLIC;
REVOKE ALL ON TABLE users FROM postgres;
GRANT ALL ON TABLE users TO postgres;
GRANT ALL ON TABLE users TO my_ottd;


--
-- Name: users_id_seq; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE users_id_seq FROM PUBLIC;
REVOKE ALL ON TABLE users_id_seq FROM postgres;
GRANT ALL ON TABLE users_id_seq TO postgres;
GRANT ALL ON TABLE users_id_seq TO my_ottd;


--
-- PostgreSQL database dump complete
--

