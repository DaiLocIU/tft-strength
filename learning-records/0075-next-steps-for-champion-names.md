# Next Steps For Champion Names

The user is ready to move from champion box detection and hex placement to champion identity.

The recommended next workflow is to reuse the current one-class champion detector, crop detected
champion boxes, label the crop folders by champion name, train a separate image classifier, then
attach the predicted name back to the chosen hex.

Champion identity should come before star-level detection because the identity signal is larger and
more important for the board-state output.
