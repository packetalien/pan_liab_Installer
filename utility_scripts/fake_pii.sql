USE YourDatabaseName; -- Replace with your actual database name

-- Create a table to hold the user information
CREATE TABLE UserInformation (
    SamAccountName VARCHAR(50),
    RODCUser VARCHAR(3),
    DomainAdmin VARCHAR(3),
    FirstName VARCHAR(50),
    LastName VARCHAR(50),
    Description VARCHAR(100),
    Department VARCHAR(50),
    Country VARCHAR(50),
    UserPrincipalName VARCHAR(100),
    [Password] VARCHAR(50),
    OU VARCHAR(100),
    Maildomain VARCHAR(50)
);

-- Insert data into the table
INSERT INTO UserInformation 
VALUES
    ('sherlockholmes', 'Yes', NULL, 'Sherlock', 'Holmes', 'Consulting Detective', 'Scotland Yard', 'United Kingdom', 'sherlockholmes@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('johnwatson', 'No', NULL, 'John', 'Watson', 'Medical Doctor', 'Medical Practice', 'United Kingdom', 'johnwatson@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('ireneadler', 'No', NULL, 'Irene', 'Adler', 'Opera Singer', NULL, 'United Kingdom', 'ireneadler@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('mycroft', 'Yes', 'Yes', 'Mycroft', 'Holmes', 'Government Official', 'Government Office', 'United Kingdom', 'mycroft@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('profchallenger', 'No', NULL, 'Professor', 'Challenger', 'Adventurer', 'Exploration Society', 'United Kingdom', 'profchallenger@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('rachelhowells', 'No', NULL, 'Rachel', 'Howells', 'Housekeeper', NULL, 'United Kingdom', 'rachelhowells@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('sigersonbell', 'No', NULL, 'Sigerson', 'Bell', 'Writer', 'Author', 'United Kingdom', 'sigersonbell@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('ireneadler2', 'No', NULL, 'Irene', 'Adler', 'Opera Singer', NULL, 'United Kingdom', 'ireneadler2@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('jamesmoriarty', 'No', NULL, 'James', 'Moriarty', 'Criminal Mastermind', 'Crime Syndicate', 'United Kingdom', 'jamesmoriarty@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('marymorstan', 'No', NULL, 'Mary', 'Morstan', 'Nurse', 'Medical Practice', 'United Kingdom', 'marymorstan@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('gregorylestrade', 'No', NULL, 'Gregory', 'Lestrade', 'Police Inspector', 'Scotland Yard', 'United Kingdom', 'gregorylestrade@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('violethunter', 'No', NULL, 'Violet', 'Hunter', 'Governess', NULL, 'United Kingdom', 'violethunter@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('charlesharker', 'No', NULL, 'Charles', 'Harker', 'Solicitor', NULL, 'United Kingdom', 'charlesharker@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('jeremiahhayling', 'No', NULL, 'Jeremiah', 'Hayling', 'Retired Sea Captain', NULL, 'United Kingdom', 'jeremiahhayling@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('ebenezerprout', 'No', NULL, 'Ebenezer', 'Prout', 'Music Teacher', NULL, 'United Kingdom', 'ebenezerprout@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('jonathansmall', 'No', NULL, 'Jonathan', 'Small', 'Criminal', NULL, 'United Kingdom', 'jonathansmall@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('elizabethholder', 'No', NULL, 'Elizabeth', 'Holder', 'Housewife', NULL, 'United Kingdom', 'elizabethholder@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('nevillesharp', 'No', NULL, 'Neville', 'Sharp', 'Journalist', NULL, 'United Kingdom', 'nevillesharp@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('jeremiahfisher', 'No', NULL, 'Jeremiah', 'Fisher', 'Boatman', NULL, 'United Kingdom', 'jeremiahfisher@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai'),
    ('ralphsmith', 'No', NULL, 'Ralph', 'Smith', 'Shopkeeper', NULL, 'United Kingdom', 'ralphsmith@democloud.ai', 'Paloalto1!', 'OU=Users', 'democloud.ai');

-- End of script
