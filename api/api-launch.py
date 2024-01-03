import sys
import traceback
import uvicorn

if __name__ == '__main__':
    print('Starting API Server: 0.0.0.0:9090')

    try:
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port="9090",
            proxy_headers=True,
            forwarded_allow_ips='*'
        )
    except KeyboardInterrupt:
        print('Exiting')
    except Exception as e:
        print('Failed to Start API')
        print('='*100)
        traceback.print_exc(file=sys.stdout)
        print('='*100)
        print('Exiting\n')
