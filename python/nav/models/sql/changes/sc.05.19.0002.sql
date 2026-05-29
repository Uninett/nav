-- Prevent the default account (id=0) from ever having is_active set to TRUE
ALTER TABLE profiles.account
    ADD CONSTRAINT default_account_never_active
    CHECK (NOT (id = 0 AND is_active));
