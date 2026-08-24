from faker import Faker

from config import FAKER_LOCALE, RANDOM_SEED

fake = Faker(FAKER_LOCALE)
Faker.seed(RANDOM_SEED)