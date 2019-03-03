CREATE TABLE IF NOT EXISTS units (
	id integer PRIMARY KEY,
	name varchar(255),
	lon numeric(6,2),
	lat numeric(6,2),
	elevation numeric(7,2),
	commission_date date,
	active boolean DEFAULT true
);

CREATE TABLE IF NOT EXISTS cameras (
	id char(6) UNIQUE,
	unit_id integer REFERENCES units (id) ON DELETE RESTRICT NOT NULL,
	commission_date date,
	active boolean DEFAULT true
);

CREATE TABLE IF NOT EXISTS sequences (
	id char(29) PRIMARY KEY,
	unit_id integer REFERENCES units (id) ON DELETE RESTRICT NOT NULL,
	start_date timestamp UNIQUE,
  	exptime numeric(6,2), 
  	pocs_version varchar(15),
  	field varchar(255),
  	state varchar(45) DEFAULT 'initial',
    dec_min numeric(7, 4),
    dec_max numeric(7, 4),
    ra_min numeric(7, 4),
    ra_max numeric(7, 4)
);
CREATE INDEX IF NOT EXISTS sequences_start_date_idex on sequences (start_date);
CREATE INDEX IF NOT EXISTS sequences_state_idx on sequences (state);
CREATE INDEX IF NOT EXISTS sequences_dec_min_dec_max_idx on sequences (dec_min, dec_max);
CREATE INDEX IF NOT EXISTS sequcnes_ra_min_ra_max_idx on sequences (ra_min, ra_max);

CREATE TABLE IF NOT EXISTS images (
	id char(29) PRIMARY KEY,
	sequence_id char(29) REFERENCES sequences (id) ON DELETE RESTRICT NOT NULL,
	camera_id char(6) REFERENCES cameras (id) ON DELETE RESTRICT NOT NULL,
	obstime timestamp,
	ra_mnt numeric(7,4), 
	ha_mnt numeric(7,4),
	dec_mnt numeric(7,4), 
	exptime numeric(6,2),
	headers jsonb,
  	file_path text,
  	state varchar(45) DEFAULT 'initial'
);
CREATE INDEX IF NOT EXISTS images_file_path_idx on images (file_path);
CREATE INDEX IF NOT EXISTS images_obstime_idx on images (obstime);
CREATE INDEX IF NOT EXISTS images_sequence_id_idx on images (sequence_id);

CREATE TABLE IF NOT EXISTS sources (
	picid bigint NOT NULL,
	image_id char(29) REFERENCES images (id) NOT NULL,
    astro_coords point,
    metadata jsonb,
	PRIMARY KEY (picid, image_id)
);
CREATE INDEX IF NOT EXISTS sources_picid_idx on sources (picid);
CREATE INDEX IF NOT EXISTS sources_image_id_idx on sources (image_id);
CREATE INDEX IF NOT EXISTS sources_astro_coords_idx on sources USING SPGIST (astro_coords);

CREATE EXTENSION IF NOT EXISTS intarray;

DROP FUNCTION normalize_source(float[]);
