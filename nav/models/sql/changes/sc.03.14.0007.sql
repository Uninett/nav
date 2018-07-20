-- Create field for storing textual representation of the interface when detaining

ALTER table arnold.identity ADD textual_interface VARCHAR DEFAULT '';
