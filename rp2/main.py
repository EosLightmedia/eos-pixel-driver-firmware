try:
    from pixel_driver import EPD
    EPD().run_scene()
except Exception as e:
    import sys, rgb_logger
    print("Critical Error", e)
    raise e
    sys.print_exception(e)
    rgb_logger.RGBLogger().system_error()
