try:
    from pixel_driver import EPD
    EPD().run_scene()
except Exception as e:
    import sys, rgb_logger
    print("Critical Error", e)
    rgb_logger.RGBLogger().system_error()
    raise e
