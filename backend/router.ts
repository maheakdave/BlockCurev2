import express,{Request,Response} from 'express';
import axios from 'axios';
import { createHash } from 'node:crypto';
const data = require('./data.json');

const router = express.Router();

router.get('/',(req:Request,res:Response)=>{
    res.send(data);
})
router.post('/',async (req:Request,res:Response)=>{
    const code = createHash('sha256').update(req.body.diagnosis+req.body.treatment).digest('hex').toString();
    try{
        const data = {"id":code,"diagnosis":req.body.diagnosis,"treatment":req.body.treatment};
        console.log(data);
        const {data:response} = await axios.post('http://localhost:8000/api',data);
        const result = response;
        console.log(response);
    }catch(e){
        console.log("Error");
    }
});
export default router;