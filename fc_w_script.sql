CREATE TABLE Analyst ( 
	AnalystID            INTEGER NOT NULL  PRIMARY KEY  ,
	Name                 TEXT     ,
	Email                TEXT     ,
	Team                 TEXT     ,
	Active               CHAR(1)     
 );

CREATE TABLE Countries ( 
	CountryID            CHAR(2) NOT NULL  PRIMARY KEY  ,
	CodeAlphaThree       CHAR(3)     ,
	NumericCode          INTEGER     ,
	DisplayName          TEXT NOT NULL    
 );

CREATE TABLE Currency ( 
	CurrencyID           CHAR(3) NOT NULL  PRIMARY KEY  ,
	Code                 INTEGER     ,
	Name                 TEXT     ,
	CurrencyType         TEXT     ,
	DecimalPlaces        INTEGER     
 );

CREATE TABLE Party ( 
	PartyID              INTEGER NOT NULL  PRIMARY KEY  ,
	PartyType            TEXT     ,
	Name                 TEXT     ,
	CountryID            CHAR(2)     ,
	FOREIGN KEY ( CountryID ) REFERENCES Countries( CountryID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

CREATE TABLE Sanction ( 
	SanctionID           INTEGER NOT NULL  PRIMARY KEY AUTOINCREMENT ,
	PartyID              INTEGER     ,
	EntityName           TEXT     ,
	CountryID            CHAR(2)     ,
	Programme            TEXT     ,
	Source               TEXT     ,
	ListedDate           DATE     ,
	DelistedDate         DATE     ,
	CONSTRAINT unq_Sanctions_Country UNIQUE ( CountryID ),
	FOREIGN KEY ( CountryID ) REFERENCES Countries( CountryID ) ON DELETE SET NULL ON UPDATE CASCADE,
	FOREIGN KEY ( PartyID ) REFERENCES Party( PartyID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

CREATE TABLE Transaction ( 
	TransactionID        INTEGER NOT NULL  PRIMARY KEY  ,
	SenderPartyID        INTEGER NOT NULL    ,
	ReceiverPartyID      INTEGER NOT NULL    ,
	MerchantPartyID      INTEGER     ,
	Amount               INTEGER NOT NULL    ,
	CurrencyID           CHAR(3) NOT NULL    ,
	TransactionDate      DATE NOT NULL    ,
	TransactionType      TEXT     ,
	OriginCountryID      CHAR(2)     ,
	CONSTRAINT unq_Transactions_Country UNIQUE ( OriginCountryID ),
	CONSTRAINT unq_Transactions_CurrencyID UNIQUE ( CurrencyID ),
	FOREIGN KEY ( OriginCountryID ) REFERENCES Countries( CountryID ) ON DELETE SET NULL ON UPDATE CASCADE,
	FOREIGN KEY ( CurrencyID ) REFERENCES Currency( CurrencyID ) ON DELETE SET NULL ON UPDATE CASCADE,
	FOREIGN KEY ( SenderPartyID ) REFERENCES Party( PartyID ) ON DELETE SET NULL ON UPDATE CASCADE,
	FOREIGN KEY ( ReceiverPartyID ) REFERENCES Party( PartyID ) ON DELETE SET NULL ON UPDATE CASCADE,
	FOREIGN KEY ( MerchantPartyID ) REFERENCES Party( PartyID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

CREATE TABLE Account ( 
	AcountID             INTEGER NOT NULL  PRIMARY KEY  ,
	PartyID              INTEGER     ,
	AccountNo            INTEGER     ,
	AccountType          TEXT     ,
	CurrencyID           CHAR(3)     ,
	OpenDate             DATE     ,
	CloseDate            DATE     ,
	Status               TEXT     ,
	FOREIGN KEY ( PartyID ) REFERENCES Party( PartyID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

CREATE TABLE Customer ( 
	CustomerID           INTEGER NOT NULL  PRIMARY KEY  ,
	PartyID              INT     ,
	Occupation           TEXT     ,
	OpenDate             DATE     ,
	RiskRating           INTEGER     ,
	FOREIGN KEY ( PartyID ) REFERENCES Party( PartyID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

CREATE TABLE CustomerRiskRating ( 
	RiskRatingID         INTEGER NOT NULL  PRIMARY KEY  ,
	CustomerID           INTEGER NOT NULL    ,
	RiskRating           TEXT NOT NULL    ,
	EffectiveFrom        DATE     ,
	EffectiveTo          DATE     ,
	Reason               TEXT     ,
	CreatedAt            DATE     ,
	FOREIGN KEY ( CustomerID ) REFERENCES Customer( CustomerID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

CREATE TABLE Alert ( 
	AlertID              INTEGER NOT NULL  PRIMARY KEY  ,
	TransactionID        INTEGER     ,
	CustomerID           INTEGER     ,
	AlertType            TEXT     ,
	RuleID               TEXT     ,
	RiskScore            INTEGER     ,
	Status               TEXT     ,
	CreatedAt            DATE     ,
	FOREIGN KEY ( CustomerID ) REFERENCES Customer( CustomerID ) ON DELETE SET NULL ON UPDATE CASCADE,
	FOREIGN KEY ( TransactionID ) REFERENCES Transaction( TransactionID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

CREATE TABLE Case ( 
	CaseID               INT NOT NULL  PRIMARY KEY  ,
	Priority             CHAR(10)     ,
	Status               CHAR(10)     ,
	AssignedAnalystID    CHAR(100)     ,
	CreatedAt            DATE     ,
	ClosedAt             DATE     ,
	Notes                TEXT     ,
	AlertID              INTEGER     ,
	FOREIGN KEY ( AlertID ) REFERENCES Alert( AlertID ) ON DELETE SET NULL ON UPDATE CASCADE,
	FOREIGN KEY ( AssignedAnalystID ) REFERENCES Analyst( AnalystID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

CREATE TABLE CaseActivity ( 
	ActivityID           INTEGER NOT NULL  PRIMARY KEY  ,
	CaseID               INTEGER     ,
	AnalystID            INTEGER     ,
	ActivityType         TEXT     ,
	Description          TEXT     ,
	CreatedAt            DATE     ,
	FOREIGN KEY ( CaseID ) REFERENCES Case( CaseID ) ON DELETE SET NULL ON UPDATE CASCADE,
	FOREIGN KEY ( AnalystID ) REFERENCES Analyst( AnalystID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

CREATE TABLE CaseCustomer ( 
	CaseID               INTEGER NOT NULL    ,
	CustomerID           INTEGER NOT NULL    ,
	CONSTRAINT pk_CaseCustomer PRIMARY KEY ( CaseID, CustomerID ),
	FOREIGN KEY ( CaseID ) REFERENCES Case( CaseID ) ON DELETE SET NULL ON UPDATE CASCADE,
	FOREIGN KEY ( CustomerID ) REFERENCES Customer( CustomerID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

CREATE TABLE CaseSanction ( 
	CaseID               INTEGER NOT NULL    ,
	SanctionID           INTEGER NOT NULL    ,
	CONSTRAINT pk_CaseSanction PRIMARY KEY ( CaseID, SanctionID ),
	FOREIGN KEY ( CaseID ) REFERENCES Case( CaseID ) ON DELETE SET NULL ON UPDATE CASCADE,
	FOREIGN KEY ( SanctionID ) REFERENCES Sanction( SanctionID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

CREATE TABLE CaseTransaction ( 
	CaseID               INTEGER NOT NULL    ,
	TransactionID        INTEGER NOT NULL    ,
	CONSTRAINT pk_CaseTransaction PRIMARY KEY ( CaseID, TransactionID ),
	FOREIGN KEY ( CaseID ) REFERENCES Case( CaseID ) ON DELETE SET NULL ON UPDATE CASCADE,
	FOREIGN KEY ( TransactionID ) REFERENCES Transaction( TransactionID ) ON DELETE SET NULL ON UPDATE CASCADE
 );

