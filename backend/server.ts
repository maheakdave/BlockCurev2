import express,{Request,Response} from 'express';
import dotenv from 'dotenv';
const cors = require('cors');
dotenv.config();
import  cluster  from 'node:cluster';
import router from './router';
import crypto from 'crypto';
import bodyParser from 'body-parser';

const getList = () =>{
    let list = new Array<number>();
    const forbiddenPorts = [3333,5173,8000];
    for(let i = 0;i<2;++i)
    {   
        let randint = crypto.randomInt(1000,9999);
        while(forbiddenPorts.includes(randint)){
            randint = crypto.randomInt(1000,9999);
        }
        list.push(randint);
    } 
    return list
}

if (cluster.isPrimary){
    const PPort = process.env.PORT; 
    const list = getList();
    for (let i = 0;i<2;++i){
        let worker = cluster.fork();
        worker.send(list[i]);
    }
    const app = express();
    app.use(cors());
    app.get('',(req:Request,res:Response)=>{
        res.send(list);
    });
    app.listen(PPort,()=>console.log(`Primary server running on Port:${PPort}`));
}
else{
    process.on('message',(msg:number)=>{
        const app = express();
        app.use(cors());
        app.use(bodyParser.json());
        app.use(router);
        app.listen(msg,()=>console.log(`Server listening on Port: ${msg}`));
    })
    }