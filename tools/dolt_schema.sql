-- Dolt schema for requirements (mirrors the Doorstop YAML items).
-- asil is nullable: only SRD items carry an ASIL; we never invent one for SWR/TST.
CREATE TABLE requirements (
  uid VARCHAR(10) PRIMARY KEY,
  type ENUM('SRD','SWR','TST') NOT NULL,
  level VARCHAR(10),
  text TEXT NOT NULL,
  asil ENUM('QM','A','B','C','D'),
  status ENUM('draft','reviewed','approved','obsolete') NOT NULL DEFAULT 'draft',
  header VARCHAR(200),
  rationale TEXT,
  verification_method ENUM('test','analysis','inspection','demonstration')
);
CREATE TABLE links (
  child_uid VARCHAR(10) NOT NULL,
  parent_uid VARCHAR(10) NOT NULL,
  PRIMARY KEY (child_uid, parent_uid)
);
