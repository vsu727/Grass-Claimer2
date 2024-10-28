import asyncio
import traceback

from core.grass import GrassFoundation
from data.config import THREADS
from utils import logger
from core import claimer


async def process_account(private_key, semaphore):
    address = ""
    async with semaphore:
        try:
            grass = GrassFoundation(private_key)
            address = grass.address

            proof = await grass.get_sign_msg()

            claim_res = await claimer(private_key=private_key, version=proof['versionNumber'], claim_proof=proof['claimProof'],
                                      allocation=proof["allocation"],
                                      )

            if claim_res:
                logger.info("Successfully claimed")

                with open(f'{path}/success.txt', 'a') as f:
                    f.write(f"{private_key}\n")

                return True
        except Exception as e:
            logger.error(f"{address} | {e} | {traceback.format_exc()}")
        finally:
            await grass.close()

        with open(f'{path}/failed.txt', 'a') as f:
            f.write(f"{private_key}\n")

async def wait_until_start(private_key: str):
    grass = GrassFoundation(private_key)
    proof = ""

    while True:
        try:
            proof = await grass.get_sign_msg()

            if proof:
                logger.success(f"Successfully started | {proof}")
                await grass.close()
                return True

        except Exception as e:
            logger.warning(f"Waiting for start | {e}")
        finally:
            logger.warning(f"Waiting for start | {proof} | {grass.address}")

        await asyncio.sleep(1)


async def main():
    keys = [account for account in open(f'{path}/keys.txt').read().splitlines()]
    # proxies = open(f'{path}/proxies.txt').read().splitlines()
    logger.info(f"Keys: {len(keys)}")

    await wait_until_start(keys[0])

    semaphore = asyncio.Semaphore(THREADS)

    tasks = []
    for i, _ in enumerate(keys):
        task = asyncio.create_task(process_account(
            keys[i],
            # proxies[i] if len(proxies) > i else None,
            semaphore
        ))
        tasks.append(task)

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    path = "data"

    asyncio.run(main())
