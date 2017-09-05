"""Main module for starting process. Here is the logic of preparation it
"""

def launch():
    import strategyexec

    def menu():
        # TODO: add class like 'key' for specify all valid strategies, use it instead constants
        strategy = {'first': 1, 'second': 2, 'third': 3}
        strategy_cancel = 0
        enter_text = "Please specify your task:"\
                        "\n- put: {} for 'Generates report on the spent hours per programmer\n\t\tand per component'"\
                        "\n- put: {} for 'Generates and send e-mails for assainees with tasks\n\t\tthat do not have estimates or component field filled in'"\
                        "\n- put: {} for 'Generates some random data'"\
                        "\n- put: {} for 'Cancel'\n> "\
                        .format(strategy['first'], strategy['second'], strategy['third'], strategy_cancel)
        wrong_text = "Invalid value, try again...\n"
        cancel_text = "Canceled"

        while True:
            try:
                nmbr = int(raw_input(enter_text))
                if nmbr == strategy_cancel:
                    print cancel_text
                    return False
                elif nmbr in (strategy['first'], strategy['second'], strategy['third']):
                    return nmbr
                else:
                    print wrong_text
            except ValueError:
                print wrong_text

    executor = None
    while True:
        key = menu()
        if key is False:
            break

        if executor is None:
            executor = strategyexec.Strategy('testingnewtask', 'tester', '123gfh09_de')

        executor.execute(key)
        print "\n\n"

    raw_input("\nProcess completed! Press Enter for close...")

if __name__ == '__main__':
    try:
        launch()
    except:
        import traceback
        print "\nUnexpected error:\n"
        traceback.print_exc()
        raw_input("\nProcess canceled. Press Enter for close...")
