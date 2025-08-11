import random
class RandomLeafGenerator:
    def __init__(self, num_leaves):
        self.num_leaves = num_leaves

    def get_random_leaf(self):
        return random.randint(0, self.num_leaves - 1)