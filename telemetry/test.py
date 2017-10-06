import logging

def main():
  logger = logging.getLogger('simple_example')
  logger.handlers = []
  fh = logging.FileHandler('spam.log')
  ch = logging.StreamHandler()
  logger.addHandler(ch)
  logger.addHandler(fh)
  logger.setLevel(logging.DEBUG)
  logger.debug('test')

if __name__ == '__main__':
  main()

